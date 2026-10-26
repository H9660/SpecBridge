"""The code library: the frozen repos stored in one SQLite file and searched by keywords.

Tables (one file, `specbridge_index.sqlite` next to the repos):
  repos, files, files_fts   whole code files and their keyword index (Step 4a)
  pieces, pieces_fts        top-level pieces (components, hooks, functions) labelled with the
                            on-screen text they use and where they appear in the app (Step 4b)
  piece_vectors             one embedding per piece and model, for search by meaning (Step 4c)
  symbols, links, packages  exported names; links between files (kind "import": relative import,
                            "package": a name imported from an @openmrs package, resolved to the
                            file that defines it, often in core; "ui": a slot / workspace / modal
                            name used in one file and registered for another in routes.json,
                            often across repos); and which repo folder each @openmrs package lives in
Everything else in SpecBridge uses `rank_files` / `search_code` (and the tools in code_tools.py)
and never reads the tables directly, so the store can be swapped without touching its callers.
`numpy` is needed only for search by meaning.

Code names are split into words before indexing ("PaginatedVitals" / "paginated-vitals" ->
"paginated vitals"), and words are stemmed ("notes" matches "note"), so ticket wording can
match code wording.
"""
import array
import json
import math
import posixpath
import re
import sqlite3
import subprocess
from dataclasses import dataclass

from specbridge import code_parse
from specbridge.env import PROJECT

SCHEMA_VERSION = 4
CODE_FILE = re.compile(r"\.(tsx?|jsx?)$")
TEST_FILE = re.compile(r"(\.test\.|\.spec\.|__mocks__/|__tests__/|(^|/)e2e/)")
NOT_A_DEFINITION = re.compile(r"(mock|\.stories\.|/index\.tsx?$)")   # re-exports and stand-ins
EXPORT_NAME = re.compile(r"^export\s+(?:default\s+)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?"
                         r"(?:function\*?|const|let|class|interface|type|enum)\s+(\w+)", re.M)
CAMEL = re.compile(r"([a-z0-9])([A-Z])")
WORD = re.compile(r"[a-z][a-z0-9]{2,}")
PATH_WEIGHT, BODY_WEIGHT = 5.0, 1.0
# pieces_fts columns: path, name, on-screen text + where it appears, code
PIECE_WEIGHTS = (5.0, 1.0, 1.0, 1.0)
# Link-following: the top LINK_SEEDS files pass a share of their score to linked files (Step 4d)
LINK_SEEDS, LINK_WEIGHTS = 5, {"ui": 0.5, "import": 0.3, "package": 0.0}
RRF_K = 60
INHERIT_DEPTH = 3   # a component imported by a widget appears on the same screen, up to this many imports down
# Common words in ticket text that say nothing about where the code is.
STOPWORDS = set("""
the and for are but not you all any can had her was one our out has have this that with from they will would there
their what about which when make like into than then them these some could other also only after before should
been being does doing done such very just more most where while each both same over under again further here
how why who whom its itself your yours ours via per get gets got use used using user users able currently
instead even still need needs needed want wants new see seen shown show shows way ways because however issue
issues ticket bug feature expected actual behavior behaviour steps step reproduce currently e.g etc http https
www com org openmrs o3 please let lets something someone link removed reference
""".split())


@dataclass
class Hit:
    repo: str
    path: str
    score: float  # higher is better


@dataclass
class PieceHit:
    id: int
    repo: str
    path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    score: float  # higher is better


def words(text):
    """Lower-case words of text, with code names split into their parts."""
    return " ".join(WORD.findall(CAMEL.sub(r"\1 \2", text).lower()))


def query_terms(text, limit=60):
    """The distinct useful words of a ticket, in the order they first appear."""
    seen = []
    for w in words(text).split():
        if w not in STOPWORDS and w not in seen:
            seen.append(w)
    return seen[:limit]


def fts_query(text):
    terms = query_terms(text)
    return " OR ".join(f'"{t}"' for t in terms) if terms else None


def git(repo_path, *args):
    return subprocess.run(["git", "-C", str(repo_path), *args], check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


class CodeIndex:
    def __init__(self, workdir, db_path=None):
        self.workdir = workdir
        self.db_path = db_path or workdir / "specbridge_index.sqlite"
        self.repos = [r["name"] for r in
                      json.loads((PROJECT / "config" / "repos.json").read_text(encoding="utf-8"))["repos"]]
        self.db = sqlite3.connect(self.db_path)
        self._matrix = None   # (model, piece ids, normalised vectors) once loaded
        self._degree = {}

    def close(self):
        self.db.close()

    def stored_commits(self):
        try:
            return dict(self.db.execute("SELECT repo, commit_sha FROM repos"))
        except sqlite3.OperationalError:
            return {}

    def current_commits(self):
        return {name: git(self.workdir / name, "rev-parse", "HEAD").strip() for name in self.repos}

    def is_current(self):
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        return version == SCHEMA_VERSION and self.stored_commits() == self.current_commits()

    def build(self, force=False):
        """(Re)build the index from the checked-out repos. Returns False if it was already up to date."""
        if not force and self.is_current():
            return False
        db = self.db
        db.executescript("""
            DROP TABLE IF EXISTS repos; DROP TABLE IF EXISTS files; DROP TABLE IF EXISTS files_fts;
            DROP TABLE IF EXISTS pieces; DROP TABLE IF EXISTS pieces_fts; DROP TABLE IF EXISTS symbols;
            DROP TABLE IF EXISTS links; DROP TABLE IF EXISTS packages; DROP TABLE IF EXISTS piece_vectors;
            CREATE TABLE repos (repo TEXT PRIMARY KEY, commit_sha TEXT NOT NULL);
            CREATE TABLE files (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, path TEXT NOT NULL,
                                is_test INTEGER NOT NULL, text TEXT NOT NULL, appears_in TEXT NOT NULL,
                                UNIQUE (repo, path));
            CREATE VIRTUAL TABLE files_fts USING fts5(path_words, body_words, tokenize = 'porter unicode61');
            CREATE TABLE pieces (id INTEGER PRIMARY KEY, file_id INTEGER NOT NULL REFERENCES files(id),
                                 name TEXT NOT NULL, kind TEXT NOT NULL, start_line INTEGER NOT NULL,
                                 end_line INTEGER NOT NULL, text TEXT NOT NULL, screen_text TEXT NOT NULL);
            CREATE INDEX pieces_file ON pieces(file_id);
            CREATE VIRTUAL TABLE pieces_fts USING fts5(path_words, name_words, ui_words, body_words,
                                                       tokenize = 'porter unicode61');
            CREATE TABLE symbols (file_id INTEGER NOT NULL REFERENCES files(id), name TEXT NOT NULL);
            CREATE INDEX symbols_name ON symbols(name);
            CREATE TABLE links (src_file_id INTEGER NOT NULL REFERENCES files(id), kind TEXT NOT NULL,
                                module TEXT NOT NULL, dst_file_id INTEGER REFERENCES files(id), names TEXT NOT NULL);
            CREATE INDEX links_src ON links(src_file_id);
            CREATE INDEX links_dst ON links(dst_file_id);
            CREATE TABLE packages (name TEXT PRIMARY KEY, repo TEXT NOT NULL, dir TEXT NOT NULL);
            CREATE TABLE piece_vectors (piece_id INTEGER NOT NULL REFERENCES pieces(id), model TEXT NOT NULL,
                                        vector BLOB NOT NULL, PRIMARY KEY (piece_id, model));
        """)
        self._matrix, self._degree = None, {}
        imports, registered, mentions = [], {}, {}
        for name, sha in self.current_commits().items():
            db.execute("INSERT INTO repos VALUES (?, ?)", (name, sha))
            i, r, m = self._build_repo(name)
            imports += i
            mentions.update(m)
            for ui_name, targets in r.items():
                registered.setdefault(ui_name, []).extend(targets)
        self._build_links(imports, registered, mentions)
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        db.commit()
        return True

    def _build_repo(self, repo):
        db, root = self.db, self.workdir / repo
        tracked = git(root, "ls-files").splitlines()
        tracked_set = set(tracked)
        read = lambda p: (root / p).read_text(encoding="utf-8", errors="replace")  # noqa: E731

        for p in tracked:   # where each @openmrs package lives
            if posixpath.basename(p) == "package.json":
                try:
                    pkg = json.loads(read(p)).get("name", "")
                except json.JSONDecodeError:
                    continue
                if pkg.startswith("@openmrs/"):
                    db.execute("INSERT OR IGNORE INTO packages VALUES (?, ?, ?)", (pkg, repo, posixpath.dirname(p)))

        appears, registered = {}, {}
        for p in tracked:
            if posixpath.basename(p) == "routes.json":
                d = posixpath.dirname(p)
                index_path = next((f"{d}/{n}" for n in ("index.ts", "index.tsx") if f"{d}/{n}" in tracked_set), None)
                for target, kind, ui_name, slots, where in code_parse.routes_entries(
                        read(p), index_path, read(index_path) if index_path else "", tracked_set):
                    appears.setdefault(target, []).append(where)
                    for n in [ui_name, *slots]:
                        if n:
                            registered.setdefault(n, []).append((repo, target))

        code_files = [p for p in tracked if CODE_FILE.search(p)]
        texts = {p: read(p) for p in code_files}
        file_imports = {p: code_parse.imports(texts[p]) for p in code_files if not TEST_FILE.search(p)}
        children = {p: [code_parse.resolve(p, m, tracked_set) for m, _ in imps] for p, imps in file_imports.items()}
        inherited = {}
        frontier = list(appears)
        for _ in range(INHERIT_DEPTH):   # pass "appears in" down to imported files that have none of their own
            nxt = []
            for parent in frontier:
                for child in children.get(parent, []):
                    if child and child not in appears and child != parent:
                        where = inherited.setdefault(child, [])
                        for w in appears.get(parent) or inherited.get(parent, []):
                            if f"inside {w}" not in where and not w.startswith("inside "):
                                where.append(f"inside {w}")
                        nxt.append(child)
            frontier = nxt

        english_cache = {}

        def english_for(path):
            d = posixpath.dirname(path)
            while True:
                if d not in english_cache:
                    en = f"{d}/translations/en.json" if d else "translations/en.json"
                    english_cache[d] = json.loads(read(en)) if en in tracked_set else None
                if english_cache[d] is not None or not d:
                    return english_cache[d] or {}
                d = posixpath.dirname(d)

        links, mentions = [], {}
        for path in code_files:
            text = texts[path]
            is_test = bool(TEST_FILE.search(path))
            where = appears.get(path) or inherited.get(path, [])
            file_id = db.execute(
                "INSERT INTO files (repo, path, is_test, text, appears_in) VALUES (?, ?, ?, ?, ?)",
                (repo, path, int(is_test), text, "\n".join(where))).lastrowid
            db.execute("INSERT INTO files_fts (rowid, path_words, body_words) VALUES (?, ?, ?)",
                       (file_id, words(f"{repo} {path}"), words(text)))
            if is_test:
                continue
            db.executemany("INSERT INTO symbols VALUES (?, ?)",
                           [(file_id, n) for n in sorted(set(EXPORT_NAME.findall(text)))])
            for module, names in file_imports[path]:
                dst = code_parse.resolve(path, module, tracked_set)
                links.append((file_id, module, (repo, dst) if dst else None, names))
            mentions[file_id] = code_parse.ui_names(text)
            english = english_for(path)
            for name, kind, start, end, body in code_parse.split_pieces(path, text):
                shown = code_parse.screen_text(body, english)
                piece_id = db.execute(
                    "INSERT INTO pieces (file_id, name, kind, start_line, end_line, text, screen_text) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", (file_id, name, kind, start, end, body, "\n".join(shown))).lastrowid
                db.execute("INSERT INTO pieces_fts (rowid, path_words, name_words, ui_words, body_words) "
                           "VALUES (?, ?, ?, ?, ?)",
                           (piece_id, words(f"{repo} {path}"), words(name),
                            words(" ".join(shown + where)), words(body)))
        return links, registered, mentions

    def _build_links(self, imports, registered, mentions):
        db = self.db
        ids = {(r, p): i for i, r, p in db.execute("SELECT id, repo, path FROM files")}
        packages = {n: (r, d) for n, r, d in db.execute("SELECT name, repo, dir FROM packages")}
        defined = {}
        for name, file_id, repo, path in db.execute(
                "SELECT s.name, f.id, f.repo, f.path FROM symbols s JOIN files f ON f.id = s.file_id"):
            if not NOT_A_DEFINITION.search(path):
                defined.setdefault(name, []).append((file_id, repo, path))
        rows = []
        for src, module, dst, names in imports:
            if dst:
                rows.append((src, "import", module, ids.get(dst), " ".join(names)))
            elif module.startswith("@openmrs/") and module in packages:
                repo, pkg_dir = packages[module]
                # @openmrs/esm-framework re-exports every framework package in core
                home = "packages/framework/" if module == "@openmrs/esm-framework" else pkg_dir + "/"
                for n in names:
                    found = sorted((d for d in defined.get(n, []) if d[1] == repo and d[2].startswith(home)),
                                   key=lambda d: len(d[2]))
                    if found and found[0][0] != src:
                        rows.append((src, "package", module, found[0][0], n))
        for src, used in mentions.items():
            for ui_name in used & registered.keys():
                for repo, path in registered[ui_name]:
                    dst = ids.get((repo, path))
                    if dst and dst != src:
                        rows.append((src, "ui", ui_name, dst, ui_name))
        db.executemany("INSERT INTO links VALUES (?, ?, ?, ?, ?)", rows)

    def neighbours(self, repo, path):
        """Files linked to this one in either direction: [(repo, path, kind, direction, via)]."""
        return self.db.execute("""
            SELECT f.repo, f.path, l.kind, 'uses', l.names FROM links l JOIN files f ON f.id = l.dst_file_id
              WHERE l.src_file_id = (SELECT id FROM files WHERE repo = ? AND path = ?)
            UNION ALL
            SELECT f.repo, f.path, l.kind, 'used by', l.names FROM links l JOIN files f ON f.id = l.src_file_id
              WHERE l.dst_file_id = (SELECT id FROM files WHERE repo = ? AND path = ?)""",
                               (repo, path, repo, path)).fetchall()

    def file_count(self, include_tests=True):
        sql = "SELECT COUNT(*) FROM files" + ("" if include_tests else " WHERE is_test = 0")
        return self.db.execute(sql).fetchone()[0]

    def piece_count(self):
        return self.db.execute("SELECT COUNT(*) FROM pieces").fetchone()[0]

    def _filters(self, repos, include_tests):
        sql, args = "", []
        if not include_tests:
            sql += " AND f.is_test = 0"
        if repos:
            sql += f" AND f.repo IN ({','.join('?' * len(repos))})"
            args += list(repos)
        return sql, args

    def search(self, text, k=20, repos=None, include_tests=False):
        """Best-matching whole files for free text (e.g. a ticket), best first."""
        query = fts_query(text)
        if not query:
            return []
        where, args = self._filters(repos, include_tests)
        sql = (f"SELECT f.repo, f.path, -bm25(files_fts, {PATH_WEIGHT}, {BODY_WEIGHT}) AS score "
               f"FROM files_fts JOIN files f ON f.id = files_fts.rowid WHERE files_fts MATCH ?{where} "
               "ORDER BY score DESC LIMIT ?")
        return [Hit(*row) for row in self.db.execute(sql, [query, *args, k])]

    def search_pieces(self, text, k=50, repos=None):
        """Best-matching pieces by keywords (name, on-screen text, where it appears, code), best first."""
        query = fts_query(text)
        if not query:
            return []
        where, args = self._filters(repos, include_tests=False)
        weights = ", ".join(str(w) for w in PIECE_WEIGHTS)
        sql = ("SELECT p.id, f.repo, f.path, p.name, p.kind, p.start_line, p.end_line, "
               f"-bm25(pieces_fts, {weights}) AS score FROM pieces_fts "
               "JOIN pieces p ON p.id = pieces_fts.rowid JOIN files f ON f.id = p.file_id "
               f"WHERE pieces_fts MATCH ?{where} ORDER BY score DESC LIMIT ?")
        return [PieceHit(*row) for row in self.db.execute(sql, [query, *args, k])]


    # --- search by meaning (Step 4c) ---------------------------------------------------------------

    def embed_text(self, piece_id):
        """What gets embedded for a piece: where it is, what it is, what the user sees, then the code."""
        repo, path, name, kind, appears, shown, body = self.db.execute(
            "SELECT f.repo, f.path, p.name, p.kind, f.appears_in, p.screen_text, p.text "
            "FROM pieces p JOIN files f ON f.id = p.file_id WHERE p.id = ?", (piece_id,)).fetchone()
        lines = [f"{repo} {path}", f"{name} ({kind})"]
        if appears:
            lines.append("Appears in: " + "; ".join(appears.splitlines()))
        if shown:
            lines.append("Screen text: " + "; ".join(shown.splitlines()))
        return "\n".join(lines) + "\n\n" + body

    def vector_count(self, model):
        return self.db.execute("SELECT COUNT(*) FROM piece_vectors WHERE model = ?", (model,)).fetchone()[0]

    def build_vectors(self, embedder, progress=None, batch=128):
        """Embed every piece that has no vector for this model yet (safe to stop and re-run)."""
        todo = [r[0] for r in self.db.execute(
            "SELECT id FROM pieces WHERE id NOT IN (SELECT piece_id FROM piece_vectors WHERE model = ?) ORDER BY id",
            (embedder.model,))]
        for i in range(0, len(todo), batch):
            ids = todo[i:i + batch]
            vectors = embedder.embed_documents([self.embed_text(pid) for pid in ids])
            self.db.executemany("INSERT INTO piece_vectors VALUES (?, ?, ?)",
                                [(pid, embedder.model, array.array("f", v).tobytes()) for pid, v in zip(ids, vectors)])
            self.db.commit()
            if progress:
                progress(min(i + batch, len(todo)), len(todo))
        self._matrix = None
        return len(todo)

    def _vectors(self, model):
        import numpy as np   # only search by meaning needs numpy
        if self._matrix is None or self._matrix[0] != model:
            rows = self.db.execute("SELECT piece_id, vector FROM piece_vectors WHERE model = ? ORDER BY piece_id",
                                   (model,)).fetchall()
            ids = np.array([r[0] for r in rows], dtype=np.int64)
            m = np.frombuffer(b"".join(r[1] for r in rows), dtype=np.float32).reshape(len(rows), -1) if rows \
                else np.zeros((0, 1), dtype=np.float32)
            m = m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)
            self._matrix = (model, ids, m)
        return self._matrix[1], self._matrix[2]

    def search_vectors(self, text, embedder, k=50):
        """Pieces closest in meaning to the text (exact search over every vector), best first."""
        import numpy as np
        ids, m = self._vectors(embedder.model)
        if not len(ids) or not text.strip():
            return []
        q = np.asarray(embedder.embed_query(text), dtype=np.float32)
        scores = m @ (q / max(float(np.linalg.norm(q)), 1e-12))
        top = np.argsort(-scores)[:k]
        found = {int(ids[i]): float(scores[i]) for i in top}
        rows = self.db.execute(
            "SELECT p.id, f.repo, f.path, p.name, p.kind, p.start_line, p.end_line FROM pieces p "
            f"JOIN files f ON f.id = p.file_id WHERE p.id IN ({','.join('?' * len(found))})", list(found)).fetchall()
        return sorted((PieceHit(*r, found[r[0]]) for r in rows), key=lambda h: h.score, reverse=True)

    # --- combined search (Step 4d) -----------------------------------------------------------------

    def _link_degree(self, repo, path):
        if (repo, path) not in self._degree:
            self._degree[(repo, path)] = len(self.neighbours(repo, path))
        return self._degree[(repo, path)]

    def follow_links(self, ranked, seeds=LINK_SEEDS, weights=LINK_WEIGHTS):
        """Re-rank files: each of the top `seeds` files passes a share of its score to the files it is
        linked to (UI wiring, imports), damped for files with very many links."""
        score = {f: 1 / (RRF_K + i) for i, f in enumerate(ranked)}
        for i, f in enumerate(ranked[:seeds]):
            for repo, path, kind, _, _ in self.neighbours(*f):
                if weights.get(kind):
                    share = weights[kind] / (RRF_K + i) / math.sqrt(max(self._link_degree(repo, path), 1))
                    score[(repo, path)] = score.get((repo, path), 0) + share
        return sorted(score, key=score.get, reverse=True)

    def rank_files(self, text, k=20, embedder=None, links=True, depth=50):
        """[(repo, path)] best first: keyword search over pieces, plus search by meaning when an embedder
        with stored vectors is given (merged by reciprocal rank), plus link-following."""
        lists = [files_from_pieces(self.search_pieces(text, 300), depth)]
        if embedder is not None and self.vector_count(embedder.model):
            lists.append(files_from_pieces(self.search_vectors(text, embedder, 300), depth))
        ranked = rrf(lists) if len(lists) > 1 else lists[0]
        return (self.follow_links(ranked) if links else ranked)[:k]

    def search_code(self, text, k=10, embedder=None, repos=None):
        """For the agent: the best files, each with its best-matching piece (name, kind, line range)."""
        hits = self.search_pieces(text, 300, repos)
        if embedder is not None and self.vector_count(embedder.model):
            hits += self.search_vectors(text, embedder, 300)
        best = {}
        for h in sorted(hits, key=lambda h: h.score, reverse=True):
            best.setdefault((h.repo, h.path), h)
        out = []
        for repo, path in self.rank_files(text, k * 3, embedder):
            if repos and repo not in repos:
                continue
            h = best.get((repo, path))
            appears = self.db.execute("SELECT appears_in FROM files WHERE repo = ? AND path = ?", (repo, path)).fetchone()
            out.append({"repo": repo, "path": path, "piece": h.name if h else None, "kind": h.kind if h else None,
                        "lines": [h.start_line, h.end_line] if h else None,
                        "appears_in": appears[0].splitlines() if appears else [],
                        "found_by": "search" if h else "link"})
            if len(out) == k:
                break
        return out


def files_from_pieces(hits, k):
    """Rank files by their best piece; [(repo, path)] best first."""
    best = {}
    for h in hits:
        best.setdefault((h.repo, h.path), h.score)
    return sorted(best, key=best.get, reverse=True)[:k]


def rrf(lists, k=RRF_K):
    """Merge ranked lists by reciprocal rank: items high in several lists come first."""
    score = {}
    for ranked in lists:
        for i, item in enumerate(ranked):
            score[item] = score.get(item, 0) + 1 / (k + i + 1)
    return sorted(score, key=score.get, reverse=True)

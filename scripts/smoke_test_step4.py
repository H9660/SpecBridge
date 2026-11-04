"""Step 4 smoke test: does the code library index the frozen repos and find the right code?

4a: every code file indexed at the frozen versions, rebuilt only when code changes, keyword search, scoring.
4b: files split into pieces labelled with on-screen text and where they appear in the app.
4c: search by meaning - plumbing tested against a fake embedding server (free, offline); live checks
    use the local Ollama model when it is running and the pieces are embedded.
4d: links (imports, @openmrs packages, UI wiring across repos), link-following search, agent tools.
Writes data/smoke_test_step4.md.
.
Usage:
  py -3.12 scripts/smoke_test_step4.py [--workdir C:/specbridge-work]
--workdir defaults to SPECBRIDGE_WORKDIR from .env. 4c checks need numpy (in .venv: .venv/bin/python).
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "scripts"))
from eval_retrieval import run, workdir_from  # noqa: E402
from specbridge.code_index import CODE_FILE, CodeIndex, query_terms, words  # noqa: E402
from specbridge.code_tools import CodeTools  # noqa: E402
from specbridge.embedder import EmbedderError, load_embedder  # noqa: E402

PASS_BAR_HIT10 = 0.80  # provisional, see docs/USER_CLARIFICATIONS.md; applies to the final Step 4 search
START_VISIT = ("patient-chart", "packages/esm-patient-chart-app/src/visit/start-visit-button.component.tsx")
BANNER = ("patient-management",
          "packages/esm-patient-search-app/src/patient-search-page/patient-banner/banner/patient-banner.component.tsx")


class FakeOllama:
    """Answers /api/embed with word-hash vectors, so texts sharing words come out close."""

    def __init__(self):
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append(body)
                raw = json.dumps({"embeddings": [outer.vector(t) for t in body["input"]]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @staticmethod
    def vector(text, dim=64):
        v = [0.0] * dim
        for w in words(text).split():
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % dim] += 1.0
        return v


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir")
    args = parser.parse_args()
    workdir = workdir_from(args.workdir)
    results = []

    def check(name, status, detail=""):
        if isinstance(status, bool):
            status = "PASS" if status else "FAIL"
        results.append((name, status, detail))

    def attempt(name, fn):
        try:
            fn()
        except Exception as err:  # a smoke test reports instead of crashing
            check(name, "FAIL", f"{type(err).__name__}: {str(err)[:200]}")

    # --- 4a: index and keyword search -------------------------------------------------------------
    snapshots = json.loads((PROJECT / "data" / "snapshots.json").read_text(encoding="utf-8"))["repos"]
    index = CodeIndex(workdir)
    index.build()
    stored = index.stored_commits()
    wrong = {n: c[:10] for n, c in stored.items() if c != snapshots[n]["commit"]}
    check("4a Index was built from the frozen version of all 5 repos",
          len(stored) == 5 and not wrong, f"{len(stored)} repos; not frozen: {wrong or 'none'}")

    expected = sum(1 for n in stored for f in subprocess.run(
        ["git", "-C", str(workdir / n), "ls-files"], capture_output=True, text=True).stdout.splitlines()
        if CODE_FILE.search(f))
    check("4a Every code file (.ts/.tsx/.js/.jsx) is in the index", index.file_count() == expected,
          f"{index.file_count()} indexed, {expected} in the repos ({index.file_count(include_tests=False)} non-test)")
    check("4a Index file lives with the repos, outside the git project",
          index.db_path.parent == workdir and PROJECT not in index.db_path.parents, str(index.db_path))
    check("4a Re-running the build skips work when the code has not changed", index.build() is False,
          "up to date, not rebuilt")
    check("4a Code names are split into words, ticket filler words dropped",
          words("PaginatedVitals paginated-vitals.component") == "paginated vitals paginated vitals component"
          and query_terms("The user should see the Vitals notes") == ["vitals", "notes"],
          f"{words('PaginatedVitals')!r}; {query_terms('The user should see the Vitals notes')}")
    hits = index.search("Add notes column to the vitals table widget", k=10)
    vitals = [h for h in hits if "esm-patient-vitals-app" in h.path]
    check("4a Hand query finds the vitals widget code in the top 10", bool(vitals),
          vitals[0].path if vitals else f"top: {[h.path for h in hits[:3]]}")
    only = index.search("appointments calendar", k=10, repos=["patient-management"])
    tests = index.search("appointments calendar", k=50, include_tests=True)
    check("4a Repo filter and test-file filter work",
          bool(only) and all(h.repo == "patient-management" for h in only)
          and any("test" in h.path or "e2e" in h.path for h in tests)
          and not any("test." in h.path for h in index.search("appointments calendar", k=50)),
          f"{len(only)} hits in patient-management only; tests appear only when asked")
    check("4a Empty or filler-only text returns nothing instead of failing",
          index.search("") == [] and index.search("the and should") == [] and index.rank_files("") == [], "[]")

    # --- 4b: pieces and labels --------------------------------------------------------------------
    db = index.db
    no_piece = db.execute("SELECT COUNT(*) FROM files f WHERE is_test = 0 AND NOT EXISTS "
                          "(SELECT 1 FROM pieces p WHERE p.file_id = f.id)").fetchone()[0]
    biggest = db.execute("SELECT MAX(LENGTH(text)) FROM pieces").fetchone()[0]
    check("4b Files are split into pieces of at most ~1,500 tokens",
          index.piece_count() > index.file_count(include_tests=False) and biggest <= 6000 and no_piece <= 5,
          f"{index.piece_count()} pieces; largest {biggest} chars; {no_piece} files with only imports have none")
    piece = db.execute("SELECT p.name, p.kind, p.start_line, p.end_line, p.screen_text FROM pieces p JOIN files f "
                       "ON f.id = p.file_id WHERE f.repo = ? AND f.path = ?", START_VISIT).fetchone()
    check("4b Pieces carry name, kind, line range and on-screen text",
          piece is not None and piece[0].startswith("StartVisitButton") and piece[1] == "component"
          and "Start visit" in piece[4], f"{piece[:4]}; text: {piece[4].splitlines()}" if piece else "not found")
    where = db.execute("SELECT appears_in FROM files WHERE repo = 'patient-chart' AND path LIKE "
                       "'%esm-patient-vitals-app/src/vitals/vitals-summary.component.tsx'").fetchone()
    labelled, inherited = db.execute("SELECT SUM(appears_in != ''), SUM(appears_in LIKE 'inside %') "
                                     "FROM files WHERE is_test = 0").fetchone()
    check("4b Files know where they appear in the app (routes.json), passed down to what they import",
          where and "widget vitals-overview-widget in patient-chart-summary-dashboard-slot" in where[0]
          and inherited > 0, f"{labelled} files labelled ({inherited} through imports); vitals summary: {where[0] if where else '-'}")

    # --- 4d: links and tools ----------------------------------------------------------------------
    kinds = dict(db.execute("SELECT kind, COUNT(*) FROM links WHERE dst_file_id IS NOT NULL GROUP BY kind"))
    links = index.neighbours(*START_VISIT)
    check("4d Links: imports, names from @openmrs packages resolved into core, UI wiring",
          all(kinds.get(k) for k in ("import", "package", "ui"))
          and any(r == "core" and k == "package" for r, _, k, _, _ in links), f"{kinds}")
    check("4d UI wiring links repos: start-visit button (patient-chart) <-> patient search banner (patient-management)",
          any((r, p) == BANNER and k == "ui" for r, p, k, _, _ in links),
          next((f"via {v}" for r, p, k, _, v in links if (r, p) == BANNER), "no link"))

    tools = CodeTools(index)
    found = tools.call("search_code", {"query": "Starting a visit from a patient search result throws", "k": 5})
    paths = [(r["repo"], r["path"]) for r in found.get("results", [])]
    check("4d Tool search_code: files with best piece, lines and where they appear",
          START_VISIT in paths and all(r["lines"] or r["found_by"] == "link" for r in found["results"]),
          f"{len(paths)} results; start-visit button at #{paths.index(START_VISIT) + 1}" if START_VISIT in paths else str(paths))
    read = tools.call("read_file", {"repo": START_VISIT[0], "path": START_VISIT[1], "start_line": 1, "end_line": 3})
    escape = tools.call("read_file", {"repo": "core", "path": "../../../etc/passwd"})
    check("4d Tool read_file reads line ranges and only files in the library",
          read.get("end_line") == 3 and read["text"].startswith("1: import") and "error" in escape,
          f"{read.get('total_lines')} lines in file; outside path -> {escape.get('error', 'no error')[:60]}")
    grep = tools.call("grep", {"pattern": "start-visit-button-slot"})
    bad = tools.call("grep", {"pattern": "(unclosed"})
    check("4d Tool grep finds exact text across repos; bad patterns give an error",
          {m["repo"] for m in grep.get("matches", [])} >= {"patient-chart", "patient-management"} and "error" in bad,
          f"{len(grep.get('matches', []))} matches")
    usages = tools.call("find_usages", {"repo": START_VISIT[0], "path": START_VISIT[1]})
    check("4d Tool find_usages lists links in both directions, across repos",
          {u["direction"] for u in usages.get("links", [])} == {"uses", "used by"}
          and len({u["repo"] for u in usages["links"]}) >= 2 and "error" in tools.call("nope", {}),
          f"{len(usages.get('links', []))} links")

    # --- 4c: search by meaning --------------------------------------------------------------------
    try:
        import numpy  # noqa: F401
        has_numpy = True
    except ImportError:
        has_numpy = False

    def fake_vectors():
        fake = FakeOllama()
        emb = load_embedder(env={}, settings={**json.loads((PROJECT / "config" / "embedder.json").read_text()),
                                              "base_url": fake.url, "model": "fake-embed", "batch_size": 64})
        tmp = pathlib.Path(tempfile.mkdtemp())
        try:
            shutil.copy(index.db_path, tmp / "copy.sqlite")
            copy = CodeIndex(workdir, tmp / "copy.sqlite")
            added = copy.build_vectors(emb, batch=512)
            again = copy.build_vectors(emb)
            hits = copy.search_vectors("start visit button patient search", emb, 10)
            hybrid = copy.rank_files("Starting a visit from a patient search result throws", 10, emb)
            prefixes = {t.split(":")[0] for r in fake.requests for t in r["input"]}
            copy.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        check("4c Every piece embedded once; re-running skips done pieces; document/query prefixes sent",
              added == index.piece_count() and again == 0 and prefixes == {"search_document", "search_query"},
              f"{added} pieces, then {again}; prefixes {sorted(prefixes)}")
        check("4c Search by meaning and hybrid search run end to end (fake vectors)",
              bool(hits) and all(a.score >= b.score for a, b in zip(hits, hits[1:])) and START_VISIT in hybrid,
              f"top piece {hits[0].name if hits else '-'}; start-visit button in hybrid top 10: {START_VISIT in hybrid}")

    if has_numpy:
        attempt("4c Search by meaning plumbing (fake embedding server)", fake_vectors)
    else:
        check("4c Search by meaning plumbing (fake embedding server)", "PENDING",
              "numpy missing - run with .venv/bin/python")

    real = load_embedder()
    try:
        a, b, c = real.embed_documents(["Start visit button on patient search", "Begin a visit from search results",
                                        "Print the billing invoice"])
        dot = lambda x, y: sum(i * j for i, j in zip(x, y)) / (sum(i * i for i in x) * sum(j * j for j in y)) ** .5  # noqa: E731
        check(f"4c Live embedder ({real.model}) works and puts similar meanings closer",
              len(a) >= 256 and dot(a, b) > dot(a, c), f"{len(a)} numbers; similar {dot(a, b):.2f} > unrelated {dot(a, c):.2f}")
        live = True
    except EmbedderError as err:
        check(f"4c Live embedder ({real.model}) works and puts similar meanings closer", "PENDING", str(err)[:160])
        live = False
    all_embedded = index.vector_count(real.model) == index.piece_count()
    index.close()

    # --- scores -----------------------------------------------------------------------------------
    stats, rows, summary = run(workdir, "keyword")
    scored = sum(r["scored"] for r in rows)
    check("4a Golden tickets scored (2 skipped: their changed files did not exist yet)",
          len(rows) == 63 and scored == 61, f"{len(rows)} tickets, {scored} scored, "
          f"skipped {[r['key'] for r in rows if not r['scored']]}")
    base = summary["all"]
    final_name = "hybrid" if live and has_numpy and all_embedded else "combined"
    stats, rows, summary = run(workdir, final_name)
    s, plain = summary["all"], summary["no file names in ticket"]
    check(f"4d Final search ({final_name}) is at least as good as the keyword baseline",
          s["hit@10"] >= base["hit@10"] and s["recall@20"] >= base["recall@20"],
          f"hit@10 {base['hit@10']:.2f} -> {s['hit@10']:.2f}; recall@20 {base['recall@20']:.2f} -> {s['recall@20']:.2f}; "
          f"cross-repo recall@20 -> {summary['group: cross-repo']['recall@20']:.2f}")
    check(f"Step 4 search reaches the provisional bar (hit@10 >= {PASS_BAR_HIT10} on tickets without file names)",
          "PASS" if plain["hit@10"] >= PASS_BAR_HIT10 else "WARN",
          f"{final_name}: hit@10 {s['hit@10']:.2f} all / {plain['hit@10']:.2f} without file names; "
          f"mrr {s['mrr']:.2f} (data/retrieval/{final_name}.md)")
    if final_name != "hybrid":
        check("4c Hybrid search (keywords + meaning + links) scored", "PENDING",
              "needs Ollama working; then run scripts/eval_retrieval.py --method hybrid with .venv/bin/python")
    check("Search is fast", stats["search_ms_per_ticket"] < 1000, f"{stats['search_ms_per_ticket']} ms per ticket")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Step 4 smoke test - {stamp}", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
    lines += [f"| {i} | {n} | {r} | {d} |" for i, (n, r, d) in enumerate(results, 1)]
    (PROJECT / "data" / "smoke_test_step4.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    raise SystemExit(1 if any(r == "FAIL" for _, r, _ in results) else 0)


if __name__ == "__main__":
    main()

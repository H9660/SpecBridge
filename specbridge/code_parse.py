"""Read OpenMRS frontend code the way the code library needs it, without a TypeScript parser.

- `split_pieces`: cut a file into top-level pieces (components, hooks, functions, types); tiny
  neighbours are merged and very long pieces are cut into parts.
- `screen_text`: the English text a piece shows, from `t('key', 'Default')` calls and the package's
  translations/en.json.
- `routes_entries`: where each file appears in the app (page, widget slot, workspace, modal), from
  routes.json and the lifecycle exports in the app's index.ts.
- `ui_names`: slot / workspace / modal names a file mentions, which link it to the files registered
  under those names, often in another repo.
- `imports`: what a file imports, so search can follow links between files and repos.
The rules rely on the repos' formatting (Prettier: top-level code starts at column 0).
"""
import json
import posixpath
import re

DECL = re.compile(r"^(?:export\s+(?:default\s+)?)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?"
                  r"(?:function\*?|const|let|var|class|interface|type|enum)\s+(\w+)|^export\s+default\b", re.M)
T_CALL = re.compile(r"""\bt\(\s*(['"`])((?:(?!\1)[^\\]|\\.)+)\1\s*(?:,\s*(['"`])((?:(?!\3)[^\\]|\\.)*)\3)?""")
IMPORT = re.compile(r"""^import\s+(?:type\s+)?([\s\S]+?)\s+from\s+['"]([^'"]+)['"]""", re.M)
SIDE_IMPORT = re.compile(r"""^import\s+['"]([^'"]+)['"]""", re.M)
DYNAMIC_IMPORT = re.compile(r"""import\(\s*['"](\.[^'"]+)['"]\s*\)""")
EXPORT_CONST = re.compile(r"^export\s+(?:const|function)\s+(\w+)", re.M)
NAME_AS = re.compile(r"(\w+)\s+as\s+(\w+)|(\w+)")
DASHED_STRING = re.compile(r"""['"`]([a-z0-9]+(?:-[a-z0-9]+)+)['"`]""")
RESOLVE_SUFFIXES = ("", ".tsx", ".ts", ".jsx", ".js", "/index.tsx", "/index.ts", "/index.js")

MIN_CHARS, MAX_CHARS = 300, 6000   # about 75 and 1,500 tokens


def kind_of(path, name):
    for suffix, kind in ((".workspace.tsx", "workspace"), (".modal.tsx", "modal"), (".resource.ts", "resource"),
                         (".resource.tsx", "resource"), ("config-schema.ts", "config"), (".extension.tsx", "extension")):
        if path.endswith(suffix):
            return kind
    if re.match(r"use[A-Z]", name or ""):
        return "hook"
    if path.endswith(".component.tsx") or (path.endswith(".tsx") and name and name[0].isupper()):
        return "component"
    return "code"


def split_pieces(path, text):
    """[(name, kind, start_line, end_line, text)] covering the file below its imports."""
    starts = [(m.start(), m.group(1) or "default") for m in DECL.finditer(text)]
    if not starts:
        return [(posixpath.basename(path), kind_of(path, None), 1, text.count("\n") + 1, text)] if text.strip() else []
    regions = []
    for (a, n), (b, _) in zip(starts, starts[1:] + [(len(text), None)]):
        regions.append([a, b, [(n, b - a)]])
    merged = []
    for r in regions:   # tiny types and constants join the piece after them
        if merged and merged[-1][1] - merged[-1][0] < MIN_CHARS:
            merged[-1][1], merged[-1][2] = r[1], merged[-1][2] + r[2]
        else:
            merged.append(r)
    if len(merged) > 1 and merged[-1][1] - merged[-1][0] < MIN_CHARS:
        last = merged.pop()
        merged[-1][1], merged[-1][2] = last[1], merged[-1][2] + last[2]
    pieces = []
    for a, b, names in merged:
        main = max(names, key=lambda n: (n[0] != "default", n[1]))[0]
        label = main if len(names) == 1 else f"{main} (+{len(names) - 1})"
        for i, (pa, pb) in enumerate(_parts(text, a, b)):
            pieces.append((label if i == 0 else f"{label} (part {i + 1})", kind_of(path, main),
                           text.count("\n", 0, pa) + 1, text.count("\n", 0, max(pb - 1, pa)) + 1, text[pa:pb]))
    return pieces


def _parts(text, a, b):
    """Cut [a, b) into parts of at most MAX_CHARS, preferring blank lines as cut points."""
    while b - a > MAX_CHARS:
        cut = text.rfind("\n\n", a + MAX_CHARS // 2, a + MAX_CHARS)
        cut = cut + 1 if cut > 0 else (text.rfind("\n", a, a + MAX_CHARS) + 1 or a + MAX_CHARS)
        yield a, cut
        a = cut
    yield a, b


def screen_text(text, english):
    """English strings a piece shows: default text in t() calls, else the en.json entry for the key."""
    out = []
    for _, key, _, default in T_CALL.findall(text):
        s = default or english.get(key) or ""
        if s and s not in out:
            out.append(s)
    return out


def imports(text):
    """[(module, [local names])] for static imports, plus dynamic import('./x') paths with no names."""
    out = []
    for names, module in IMPORT.findall(text):
        locals_ = [m[2] or m[3] for m in NAME_AS.finditer(names.replace("type ", ""))]
        out.append((module, locals_))
    out += [(m, []) for m in SIDE_IMPORT.findall(text)]
    out += [(m, []) for m in DYNAMIC_IMPORT.findall(text)]
    return out


def resolve(from_path, module, files):
    """Repo-relative file a relative import points at, or None."""
    if not module.startswith("."):
        return None
    base = posixpath.normpath(posixpath.join(posixpath.dirname(from_path), module))
    return next((base + s for s in RESOLVE_SUFFIXES if base + s in files), None)


def lifecycle_files(index_path, index_text, files):
    """Export name in an app's index.ts -> the file it renders (via import('./x') or an imported component)."""
    imported = {}
    for module, names in imports(index_text):
        target = resolve(index_path, module, files)
        for n in names:
            imported.setdefault(n, target)
    out = {}
    marks = list(EXPORT_CONST.finditer(index_text))
    for m, nxt in zip(marks, marks[1:] + [None]):
        body = index_text[m.end():nxt.start() if nxt else len(index_text)]
        dyn = DYNAMIC_IMPORT.search(body)
        target = resolve(index_path, dyn.group(1), files) if dyn else None
        if not target:
            target = next((imported[w] for w in re.findall(r"\w+", body) if imported.get(w)), None)
        if target:
            out[m.group(1)] = target
    return out


def routes_entries(routes_text, index_path, index_text, files):
    """[(file, kind, name, slots, description)] for one app's routes.json; kind is widget/page/workspace/modal."""
    try:
        routes = json.loads(routes_text)
    except json.JSONDecodeError:
        return []
    exports = lifecycle_files(index_path, index_text, files) if index_text else {}
    out = []

    def add(component, kind, name, slots, description):
        target = exports.get(component)
        if target:
            out.append((target, kind, name, slots, description))

    for e in routes.get("extensions", []):
        slots = [s for s in (e.get("slots") or [e.get("slot", "")]) if s]
        title = (e.get("meta") or {}).get("title", "")
        add(e.get("component"), "widget", e.get("name", ""), slots,
            f"widget {e.get('name', '')} in {' / '.join(slots)}" + (f" titled {title}" if isinstance(title, str) and title else ""))
    for p in routes.get("pages", []):
        route = p.get("route") if isinstance(p.get("route"), str) else p.get("routeRegex")
        add(p.get("component"), "page", "", [], f"page {route}" if route else "page on every screen")
    for w in routes.get("workspaces", []) + routes.get("workspaces2", []):
        add(w.get("component"), "workspace", w.get("name", ""), [],
            f"workspace {w.get('name', '')}" + (f" titled {w['title']}" if w.get("title") else ""))
    for m in routes.get("modals", []):
        add(m.get("component"), "modal", m.get("name", ""), [], f"modal {m.get('name', '')}")
    return out


def ui_names(text):
    """Dashed string literals in code ('patient-banner-actions-slot', 'visit-form-workspace', ...)."""
    return set(DASHED_STRING.findall(text))

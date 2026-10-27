"""Report a candidate repo against the selection criteria (handoff §3.1).

Shallow-clones the repo (optionally at a pinned commit) into a temp folder and reports: TS/TSX/JS/JSX file
count and lines, detected router type, route count, open GitHub issues (via `gh`, if installed) and licence.
It only reads files; nothing in the clone is installed or run.

    uv run python scripts/repo_stats.py https://github.com/openmrs/openmrs-esm-patient-chart.git \
        --commit 8ede2e3a641d470abcd31fe496f5714f2b4fc600
    uv run python scripts/repo_stats.py --snapshots   # every repo in data/snapshots.json at its pinned commit
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

PROJECT = pathlib.Path(__file__).resolve().parent.parent
CODE_EXT = {".ts", ".tsx", ".js", ".jsx"}
SKIP_DIRS = {"node_modules", "dist", "build", ".next", "coverage", ".git"}
TEST_RE = re.compile(r"\.(test|spec|stories)\.|\.d\.ts$|(^|/)(__tests__|__mocks__|e2e)/")
MAX_FILES = 3000
PERMISSIVE = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"}
WEAK_COPYLEFT = {"MPL-2.0", "LGPL-2.1", "LGPL-3.0", "EPL-2.0"}  # reported as NO; acceptability is the team's call
LICENSE_HINTS = [("MPL-2.0", "mozilla public license"), ("Apache-2.0", "apache license"),
                 ("MIT", "mit license"), ("AGPL-3.0", "gnu affero general public license"),
                 ("GPL-3.0", "gnu general public license"), ("BSD-3-Clause", "redistribution and use in source"),
                 ("ISC", "isc license")]


def run(*cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True).stdout.strip()


def clone(url, commit, dest):
    run("git", "init", "-q", str(dest))
    run("git", "remote", "add", "origin", url, cwd=dest)
    run("git", "fetch", "-q", "--depth", "1", "origin", commit or "HEAD", cwd=dest)
    run("git", "checkout", "-q", "FETCH_HEAD", cwd=dest)
    return run("git", "rev-parse", "HEAD", cwd=dest)


def code_files(root):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if path.is_file() and path.suffix in CODE_EXT and not SKIP_DIRS & set(rel.parts):
            yield rel.as_posix(), path


def router_stats(root, files):
    """Detect routing style(s) and count routes. A repo can use more than one."""
    found = {}
    rr_route = re.compile(r"<Route\b[^>]*\bpath\s*=")
    rr_config = re.compile(r"\b(createBrowserRouter|createHashRouter|useRoutes)\s*\(")
    rr_path = re.compile(r"""\bpath\s*:\s*['"`]""")
    rr_count, rr_files = 0, 0
    for _, path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "react-router" in text or rr_config.search(text):
            n = len(rr_route.findall(text)) + (len(rr_path.findall(text)) if rr_config.search(text) else 0)
            rr_count, rr_files = rr_count + n, rr_files + 1
    if rr_files:
        found["react-router"] = {"files_importing": rr_files, "routes": rr_count}

    next_pages = [r for r, _ in files if re.search(r"(^|/)(app/.*/page|pages/(?!api/)[^_].*)\.(t|j)sx?$", r)]
    if next_pages and any('"next"' in p.read_text(errors="ignore") for p in root.rglob("package.json")
                          if "node_modules" not in p.parts):
        found["next.js"] = {"routes": len(next_pages)}

    routes_json = [p for p in root.rglob("routes.json") if not SKIP_DIRS & set(p.relative_to(root).parts)]
    if routes_json:  # OpenMRS 3 / single-spa: each app registers pages, extensions, workspaces, modals
        totals = {"apps": len(routes_json), "pages": 0, "extensions": 0, "workspaces": 0, "modals": 0}
        for p in routes_json:
            data = json.loads(p.read_text(encoding="utf-8", errors="ignore") or "{}")
            for key in ("pages", "extensions", "workspaces", "modals"):
                totals[key] += len(data.get(key, []))
        found["single-spa routes.json"] = totals
    return found


def licence(root, url):
    spdx = None
    slug = github_slug(url)
    if slug and shutil.which("gh"):
        spdx = run("gh", "api", f"repos/{slug}", "--jq", ".license.spdx_id // empty", check=False) or None
    files = [p for p in root.iterdir() if p.is_file() and p.name.upper().startswith(("LICENSE", "LICENCE", "COPYING"))]
    if spdx in (None, "NOASSERTION") and files:  # GitHub could not classify it: read the file
        text = files[0].read_text(errors="ignore")
        found = next((k for k, hint in LICENSE_HINTS if hint in text[:3000].lower()), None)
        if found and "disclaimer" in text.lower():
            found += " + disclaimer (GitHub: NOASSERTION)"
        spdx = found or spdx or "unknown"
    return spdx or "none found", [f.name for f in files]


def open_issues(url):
    slug = github_slug(url)
    if not slug or not shutil.which("gh"):
        return None, "gh not available"
    info = run("gh", "api", f"repos/{slug}", "--jq", "[.has_issues, .open_issues_count] | @tsv", check=False)
    issues = run("gh", "api", "-X", "GET", "search/issues", "-f", f"q=repo:{slug} type:issue state:open",
                 "--jq", ".total_count", check=False)
    has_issues = info.split("\t")[0] if info else "?"
    note = "GitHub issues enabled" if has_issues == "true" else \
        "GitHub issues DISABLED - the project tracks issues elsewhere; check it by hand"
    return (int(issues) if issues.isdigit() else None), note


def github_slug(url):
    m = re.search(r"github\.com[/:]([^/]+/[^/]+?)(\.git)?$", url)
    return m.group(1) if m else None


def stats(url, commit=None, keep=None):
    tmp = pathlib.Path(keep or tempfile.mkdtemp(prefix="repo_stats_"))
    try:
        head = clone(url, commit, tmp)
        files = list(code_files(tmp))
        product = [(r, p) for r, p in files if not TEST_RE.search(r)]
        loc = sum(sum(1 for line in p.open(errors="ignore") if line.strip()) for _, p in product)
        by_ext = {}
        for r, _ in product:
            by_ext[pathlib.Path(r).suffix] = by_ext.get(pathlib.Path(r).suffix, 0) + 1
        spdx, licence_files = licence(tmp, url)
        issues, issues_note = open_issues(url)
        return {"url": url, "commit": head, "code_files_all": len(files), "code_files_non_test": len(product),
                "by_ext": by_ext, "loc_non_test": loc, "routers": router_stats(tmp, product),
                "open_github_issues": issues, "issues_note": issues_note, "licence": spdx,
                "licence_files": licence_files}
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)


def verdict(s):
    ts = s["by_ext"].get(".ts", 0) + s["by_ext"].get(".tsx", 0)
    routed = bool(s["routers"])
    return [
        ("React + TypeScript", ts > 0 and s["by_ext"].get(".tsx", 0) > 0, f"{ts} .ts/.tsx files"),
        ("Multiple routes/screens", routed, ", ".join(s["routers"]) or "no router detected"),
        ("Active issue tracker", (s["open_github_issues"] or 0) > 0,
         f"{s['open_github_issues']} open GitHub issues ({s['issues_note']})"),
        (f"Under {MAX_FILES} TS/TSX files", s["code_files_non_test"] < MAX_FILES,
         f"{s['code_files_non_test']} non-test code files"),
        ("Permissive licence", s["licence"].split(" ")[0] in PERMISSIVE, licence_detail(s["licence"])),
    ]


def licence_detail(spdx):
    return f"weak copyleft: {spdx}" if spdx.split(" ")[0] in WEAK_COPYLEFT else spdx


def report(s):
    lines = [f"## {s['url']}", f"- Commit: `{s['commit']}`",
             f"- Code files: {s['code_files_non_test']} non-test ({s['code_files_all']} incl. tests) {s['by_ext']}",
             f"- Lines (non-blank, non-test): {s['loc_non_test']:,}",
             f"- Routers: {json.dumps(s['routers'])}", f"- Licence: {s['licence']} {s['licence_files']}",
             "", "| Criterion | Meets | Detail |", "|---|---|---|"]
    lines += [f"| {name} | {'yes' if ok else 'NO'} | {detail} |" for name, ok, detail in verdict(s)]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url", nargs="?", help="Git URL of the candidate repo")
    ap.add_argument("--commit", help="Pinned commit (default: default branch HEAD)")
    ap.add_argument("--snapshots", action="store_true", help="Every repo in data/snapshots.json at its commit")
    ap.add_argument("--json", type=pathlib.Path, help="Also write the raw stats here")
    args = ap.parse_args()
    if args.snapshots:
        repos = json.loads((PROJECT / "data" / "snapshots.json").read_text())["repos"]
        targets = [(info["url"], info["commit"]) for info in repos.values()]
    elif args.url:
        targets = [(args.url, args.commit)]
    else:
        ap.error("give a URL or --snapshots")
    results = []
    for url, commit in targets:
        print(f"... {url}", file=sys.stderr)
        results.append(stats(url, commit))
        print(report(results[-1]) + "\n")
    if len(results) > 1:
        total = sum(r["code_files_non_test"] for r in results)
        print(f"**Combined:** {total} non-test code files, {sum(r['loc_non_test'] for r in results):,} lines "
              f"({'under' if total < MAX_FILES else 'OVER'} the {MAX_FILES}-file guide)")
    if args.json:
        args.json.write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

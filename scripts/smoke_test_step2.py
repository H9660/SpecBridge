"""Step 2 smoke test: is the workspace set up correctly?

Checks the downloaded repos, git hygiene, the ticket copier, and (once .env exists) the team's
Atlassian site. Writes data/smoke_test_step2.md.

Usage:
  py -3.12 scripts/smoke_test_step2.py
"""
import datetime
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge.atlassian import REQUIRED, Atlassian, missing_settings  # noqa: E402
from specbridge.env import load_env  # noqa: E402
import import_tickets  # noqa: E402

PROJECT = pathlib.Path(__file__).resolve().parent.parent


def git(path, *args):
    return subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=path,
                          capture_output=True, text=True, encoding="utf-8")


def main():
    env = load_env()
    workdir = pathlib.Path(env.get("SPECBRIDGE_WORKDIR") or "C:/specbridge-work")
    config = json.loads((PROJECT / "config" / "repos.json").read_text(encoding="utf-8"))
    snapshots = json.loads((PROJECT / "data" / "snapshots.json").read_text(encoding="utf-8"))["repos"]
    candidates = {c["key"]: c for c in json.loads(
        (PROJECT / "data" / "golden" / "candidates_v0.json").read_text(encoding="utf-8"))}
    picked = json.loads((PROJECT / "data" / "golden" / "picked_v0.json").read_text(encoding="utf-8"))["picked"]
    results = []

    def check(name, status, detail):
        if isinstance(status, bool):
            status = "PASS" if status else "FAIL"
        results.append((name, status, detail))

    # 1. Workspace folder
    check("Download folder exists and is outside OneDrive",
          workdir.is_dir() and "onedrive" not in str(workdir.resolve()).lower(), str(workdir))

    # 2. Each repo on its frozen version, complete and untouched
    problems = []
    for repo in config["repos"]:
        name, path = repo["name"], workdir / repo["name"]
        want = snapshots[name]["commit"]
        head = git(path, "rev-parse", "HEAD").stdout.strip()
        branch = git(path, "branch", "--show-current").stdout.strip()
        dirty = git(path, "status", "--porcelain").stdout.strip()
        missing = git(path, "ls-files", "--deleted").stdout.strip()
        longpaths = git(path, "config", "core.longpaths").stdout.strip()
        if head != want:
            problems.append(f"{name}: on {head[:10]}, expected {want[:10]}")
        if branch != "snapshot":
            problems.append(f"{name}: branch '{branch}'")
        if dirty or missing:
            problems.append(f"{name}: files changed or missing")
        if longpaths != "true":
            problems.append(f"{name}: long paths off")
    check("All repos on their frozen version, complete, unchanged", not problems,
          "; ".join(problems) or f"{len(config['repos'])}/{len(config['repos'])} OK")

    # 3. The code each golden ticket touched is on disk
    expected = present = 0
    for p in picked:
        for repo, files in candidates[p["key"]]["changed_code_files"].items():
            for f in files:
                if git(workdir / repo, "cat-file", "-e", f"snapshot:{f}").returncode == 0:
                    expected += 1
                    present += (workdir / repo / f).is_file()
    check("Files the golden tickets touched are readable on disk", expected == present,
          f"{present}/{expected} files")

    # 4. Git hygiene in the project folder
    nested = [str(p.parent.relative_to(PROJECT)) for p in PROJECT.rglob(".git") if p.parent != PROJECT]
    # only files git would track: the git-ignored .venv and data/runs are expected to be large
    tracked = git(PROJECT, "ls-files", "--cached", "--others", "--exclude-standard", "-z").stdout.split("\0")
    size_mb = sum((PROJECT / f).stat().st_size for f in tracked if f and (PROJECT / f).is_file()) / 1e6
    check("No downloaded repos inside the (OneDrive) project folder", not nested and size_mb < 5,
          f"{size_mb:.1f} MB of project files; nested repos: {nested or 'none'}")
    check("Secrets file (.env) is git-ignored", git(PROJECT, "check-ignore", "-q", ".env").returncode == 0, ".gitignore")
    check(".env is not tracked by git", not git(PROJECT, "ls-files", ".env").stdout.strip(), "")
    example = (PROJECT / ".env.example").read_text(encoding="utf-8")
    absent = [k for k in REQUIRED if f"{k}=" not in example]
    check(".env.example lists every setting", not absent, ", ".join(absent) or ", ".join(REQUIRED))

    # 5. Ticket copier, offline
    sample = {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "See open PR "}, {"type": "text", "text": "#12", "marks": []},
        {"type": "text", "text": " and "},
        {"type": "text", "text": "this fix", "marks": [{"type": "link", "attrs": {"href": "https://github.com/o/r/pull/9"}}]},
        {"type": "inlineCard", "attrs": {"url": "https://openmrs.atlassian.net/browse/O3-1"}},
        {"type": "mention", "attrs": {"id": "x", "text": "@dev"}},
    ]}, {"type": "mediaSingle", "content": [{"type": "media", "attrs": {"id": "m"}}]}]}
    removed = {"pr_links": 0, "source_links": 0, "attachments": 0, "mentions": 0}
    out = json.dumps(import_tickets.clean(sample, removed))
    leaks = [s for s in ("#12", "github.com", "openmrs.atlassian.net", "@dev", '"media') if s in out]
    check("Copier removes PR refs, links back, mentions, attachments (built-in example)", not leaks,
          f"leaked: {leaks}" if leaks else str(removed))

    source = import_tickets.fetch_source([p["key"] for p in picked])
    payloads, report = import_tickets.build_payloads(picked, source)
    blob = json.dumps(payloads)
    bad_doc = [p["source"] for p in payloads if p["description"].get("type") != "doc"]
    summaries = [p["summary"] for p in payloads]
    leftovers = (len(re.findall(r"github\.com/[^\"]+/pull/", blob)) + blob.count("openmrs.atlassian.net")
                 + len(re.findall(r'"type": "media', blob)) + sum(r["leftover_pr_refs"] for r in report))
    check("All 63 tickets prepared with valid descriptions", len(payloads) == len(picked) and not bad_doc,
          f"{len(payloads)} prepared; invalid: {bad_doc or 'none'}")
    check("No answer-revealing links left in any copied ticket", leftovers == 0, f"{leftovers} left")
    check("Ticket titles are unique (needed so re-runs don't duplicate)", len(set(summaries)) == len(summaries),
          f"{len(set(summaries))} unique of {len(summaries)}")
    flagged = [r["source"] for r in report if "mentions-files" in r["flags"]]
    results.append(("Tickets that name code files (flagged, kept as written)", "WARN" if flagged else "PASS",
                    f"{len(flagged)}: {', '.join(flagged)}"))

    # 6. Team's Atlassian site (needs the user's account)
    if missing_settings(env):
        for name in ("Can log in to the team's Atlassian site", "Jira project exists with Story/Task types",
                     "Confluence space exists", "All 63 tickets copied into team Jira"):
            check(name, "PENDING", "waiting for .env (user creates the Atlassian site)")
    else:
        site = Atlassian(env)
        try:
            me = site.whoami()
            check("Can log in to the team's Atlassian site", True, me.get("displayName", ""))
            types = site.issue_types()
            check("Jira project exists with Story/Task types", bool({"Story", "Task"} & set(types)),
                  f"{site.project}: {sorted(types)}")
            space = site.confluence_space()
            check("Confluence space exists", bool(space), f"{site.space}: {space['name'] if space else 'not found'}")
            copied = site.search(f'project = {site.project} AND labels = "{import_tickets.LABEL}"')
            check("All 63 tickets copied into team Jira", len(copied) == len(picked),
                  f"{len(copied)}/{len(picked)} (run scripts/import_tickets.py)")
        except Exception as err:  # report rather than crash: this is a smoke test
            check("Can log in to the team's Atlassian site", False, str(err)[:200])

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Step 2 smoke test - {stamp}", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
    lines += [f"| {i} | {n} | {r} | {d} |" for i, (n, r, d) in enumerate(results, 1)]
    (PROJECT / "data" / "smoke_test_step2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    raise SystemExit(1 if any(r == "FAIL" for _, r, _ in results) else 0)


if __name__ == "__main__":
    main()

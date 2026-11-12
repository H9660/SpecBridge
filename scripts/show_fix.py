"""Show how the OpenMRS developers really fixed a golden ticket: the answer key for the agent's evals.

For each SPEC ticket copied from the OpenMRS Jira (SPEC-1..63), data/golden/candidates_v0.json holds the original
O3 ticket, the fix commits and the code files they changed. This prints them with links to GitHub, and can show the
diff from the local clones - read-only: the frozen `snapshot` checkouts are never changed.

Usage:
  .venv/bin/python scripts/show_fix.py SPEC-12            # commits, pull requests and changed files
  .venv/bin/python scripts/show_fix.py SPEC-12 --diff     # plus the code diff of the changed files (git show)
  .venv/bin/python scripts/show_fix.py --all              # writes data/golden/fixes_v0.md: all 63 tickets
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge.env import PROJECT, load_env  # noqa: E402

GOLDEN = PROJECT / "data" / "golden"
PR = re.compile(r"\(#(\d+)\)")


def load():
    mapping = json.loads((GOLDEN / "jira_import_map.json").read_text(encoding="utf-8"))           # O3 -> SPEC
    candidates = json.loads((GOLDEN / "candidates_v0.json").read_text(encoding="utf-8"))
    items = candidates if isinstance(candidates, list) else candidates.get("candidates") or candidates.get("tickets")
    by_key = {c["key"]: c for c in items}
    groups = {p["key"]: p["group"] for p in json.loads((GOLDEN / "picked_v0.json").read_text(encoding="utf-8"))["picked"]}
    repos = json.loads((PROJECT / "data" / "snapshots.json").read_text(encoding="utf-8"))["repos"]
    tickets = {}
    for o3, spec in mapping.items():
        c = by_key.get(o3)
        if c:
            tickets[spec] = {**c, "spec": spec, "group": groups.get(o3, "")}
    return tickets, repos


def github(repos, repo):
    url = repos.get(repo, {}).get("url", "")
    return url[:-4] if url.endswith(".git") else url


def links(repos, commit):
    base = github(repos, commit["repo"])
    pr = PR.search(commit.get("subject", ""))
    return f"{base}/commit/{commit['sha']}", (f"{base}/pull/{pr.group(1)}" if pr else None)


def print_one(t, repos, diff, workdir):
    print(f"{t['spec']}  ({t['group']})  {t['summary']}")
    print(f"original ticket: {t['url']}   resolved {t.get('resolved', '?')}")
    for c in t.get("commits", []):
        commit_url, pr_url = links(repos, c)
        print(f"\n  {c['repo']}  {c['sha'][:10]}  {c.get('date', '')}  {c.get('subject', '')}")
        print(f"    commit: {commit_url}" + (f"\n    pull request: {pr_url}" if pr_url else ""))
    print("\nchanged code files (what the agent should find):")
    for repo, files in t.get("changed_code_files", {}).items():
        for f in files:
            print(f"  {repo}/{f}")
    if not diff:
        return
    for c in t.get("commits", []):
        files = t.get("changed_code_files", {}).get(c["repo"], [])
        repo_dir = workdir / c["repo"]
        print(f"\n===== {c['repo']} {c['sha'][:10]}: {c.get('subject', '')} =====")
        result = subprocess.run(["git", "-C", str(repo_dir), "show", "--stat", "--patch", "--format=%H%n%an, %ad%n%s%n",
                                 c["sha"], "--", *files], capture_output=True, text=True)
        print(result.stdout if result.returncode == 0 else f"(could not show it: {result.stderr.strip()[:300]})")


def write_all(tickets, repos):
    order = sorted(tickets, key=lambda k: int(k.split("-")[1]))
    lines = ["# How the developers fixed the golden tickets (the answer key)", "",
             "For each SPEC ticket copied from the OpenMRS Jira: the original O3 ticket, the real fix commits and pull "
             "requests on GitHub, and the number of code files they changed. The agent reads the code at the frozen "
             "commit *before* these fixes; the eval compares what it finds with these files. Made by "
             "`scripts/show_fix.py --all`; for one ticket's file list and diff: `scripts/show_fix.py SPEC-12 --diff`.",
             "", "The trick tickets (SPEC-64..69) and the edge-case tickets (`test_tickets_v1.json`) were written by "
             "hand, so they have no real fix; their expected results are in their JSON files.", "",
             "| Ticket | Group | Original | Summary | Fix (pull request / commit) | Files |", "|---|---|---|---|---|---|"]
    for spec in order:
        t = tickets[spec]
        fixes = []
        for c in t.get("commits", []):
            commit_url, pr_url = links(repos, c)
            label = f"{c['repo']} #{PR.search(c['subject']).group(1)}" if pr_url else f"{c['repo']} {c['sha'][:7]}"
            fixes.append(f"[{label}]({pr_url or commit_url})")
        n = sum(len(v) for v in t.get("changed_code_files", {}).values())
        summary = t["summary"].replace("|", "/")
        lines.append(f"| {spec} | {t['group']} | [{t['key']}]({t['url']}) | {summary[:90]} | {', '.join(fixes)} | {n} |")
    out = GOLDEN / "fixes_v0.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(PROJECT)} ({len(order)} tickets)")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the real fix of a golden ticket.")
    parser.add_argument("ticket", nargs="?", help="e.g. SPEC-12")
    parser.add_argument("--diff", action="store_true", help="also show the code diff from the local clones")
    parser.add_argument("--all", action="store_true", help="write data/golden/fixes_v0.md for every ticket")
    args = parser.parse_args(argv)
    tickets, repos = load()
    if args.all:
        write_all(tickets, repos)
        return 0
    key = (args.ticket or "").upper()
    if key not in tickets:
        print(f"{key or 'a ticket'}: not a golden ticket with a known fix (SPEC-1..SPEC-63)")
        return 2
    workdir = pathlib.Path(load_env().get("SPECBRIDGE_WORKDIR") or PROJECT.parent / "specbridge-work")
    print_one(tickets[key], repos, args.diff, workdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Step 1 smoke test: is the test data (pinned repos + shortlisted tickets) sound?

Checks everything against the live sources (GitHub + public OpenMRS Jira), not against
the builder's own output, and writes data/golden/smoke_test_step1.md.

Usage:
  py -3.12 scripts/smoke_test_step1.py --workdir <same folder used by build_ticket_shortlist.py>
"""
import argparse
import datetime
import json
import pathlib
import subprocess
import urllib.parse
import urllib.request

PROJECT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = PROJECT / "data" / "golden"


def git(path, *args):
    return subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=path,
                          capture_output=True, text=True, encoding="utf-8")


def jira_tickets(base_url, keys):
    found = {}
    for i in range(0, len(keys), 50):
        query = urllib.parse.urlencode({"jql": f"key in ({','.join(keys[i:i + 50])})",
                                        "fields": "status,description", "maxResults": 100})
        with urllib.request.urlopen(f"{base_url}/rest/api/3/search/jql?{query}", timeout=60) as resp:
            for issue in json.load(resp)["issues"]:
                found[issue["key"]] = issue["fields"]
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True, type=pathlib.Path)
    args = parser.parse_args()

    config = json.loads((PROJECT / "config" / "repos.json").read_text(encoding="utf-8"))
    snapshots = json.loads((PROJECT / "data" / "snapshots.json").read_text(encoding="utf-8"))
    picked = json.loads((GOLDEN / "picked_v0.json").read_text(encoding="utf-8"))["picked"]
    candidates = {c["key"]: c for c in json.loads((GOLDEN / "candidates_v0.json").read_text(encoding="utf-8"))}
    cutoff = config["cutoff"]
    results, warnings = [], []

    def check(name, ok, detail):
        results.append((name, "PASS" if ok else "FAIL", detail))

    # 1. Repos
    names = [r["name"] for r in config["repos"]]
    check("Config lists 4-5 repos", 4 <= len(names) <= 5, ", ".join(names))
    reachable = [n for r in config["repos"] for n in [r["name"]]
                 if git(None, "ls-remote", "--heads", r["url"]).returncode == 0]
    check("Every repo reachable on GitHub", len(reachable) == len(names), f"{len(reachable)}/{len(names)}")

    # 2. Snapshots
    bad = []
    for name in names:
        snap = snapshots["repos"].get(name, {}).get("commit", "")
        path = args.workdir / name
        exists = git(path, "cat-file", "-e", f"{snap}^{{commit}}").returncode == 0
        date = git(path, "log", "-1", "--format=%cs", snap).stdout.strip() if exists else ""
        on_main = git(path, "merge-base", "--is-ancestor", snap, "origin/HEAD").returncode == 0 if exists else False
        if not (exists and date < cutoff and on_main):
            bad.append(f"{name} (exists={exists}, date={date}, on main={on_main})")
    check("Each repo pinned to a real commit on main, dated before cutoff", not bad, "; ".join(bad) or f"all {len(names)} before {cutoff}")

    # 3. Tickets
    keys = [p["key"] for p in picked]
    check("No duplicate tickets in shortlist", len(keys) == len(set(keys)), f"{len(keys)} tickets")
    check("Shortlist has enough tickets for a 30-50 golden set", len(keys) >= 30, f"{len(keys)}")
    live = jira_tickets(config["jira"]["base_url"], keys)
    not_found = [k for k in keys if k not in live]
    check("Every ticket exists in public Jira", not not_found, ", ".join(not_found) or f"{len(live)}/{len(keys)}")
    not_done = [k for k in live if live[k]["status"]["name"] != "Done"]
    check("Every ticket is finished (Done)", not not_done, ", ".join(not_done) or "all Done")
    no_text = [k for k in live if not live[k].get("description")]
    check("Every ticket has a description", not no_text, ", ".join(no_text) or "all have text")

    leaked, none_existing, coverage = [], [], []
    for key in keys:
        c = candidates[key]
        for commit in c["commits"]:
            path = args.workdir / commit["repo"]
            snap = snapshots["repos"][commit["repo"]]["commit"]
            if git(path, "merge-base", "--is-ancestor", commit["sha"], snap).returncode == 0:
                leaked.append(f"{key}@{commit['repo']}")
        total = existing = 0
        for repo, files in c["changed_code_files"].items():
            snap = snapshots["repos"][repo]["commit"]
            for f in files:
                total += 1
                existing += git(args.workdir / repo, "cat-file", "-e", f"{snap}:{f}").returncode == 0
        coverage.append(existing / total if total else 0)
        if existing == 0:
            none_existing.append(key)
    check("No ticket's fix is already inside the frozen code", not leaked, ", ".join(leaked) or "0 leaks")
    avg = sum(coverage) / len(coverage)
    results.append(("Changed files exist in frozen code (something real to find)",
                    "PASS" if not none_existing else "WARN",
                    f"avg {avg:.0%} of changed files already existed; {len(none_existing)} tickets only add new files"))
    if none_existing:
        warnings.append("Tickets whose changes are all new files (SpecBridge can only point to the nearby screen, "
                        "not an existing file): " + ", ".join(none_existing))

    # 4. Readable shortlist matches the data
    rows = sum(1 for line in (GOLDEN / "shortlist_v0.md").read_text(encoding="utf-8").splitlines()
               if line.startswith("| [O3-"))
    check("Readable shortlist matches the data", rows == len(keys), f"{rows} rows vs {len(keys)} picked")

    # Report
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Step 1 smoke test - {stamp}", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
    lines += [f"| {i} | {n} | {r} | {d} |" for i, (n, r, d) in enumerate(results, 1)]
    if warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in warnings]
    (GOLDEN / "smoke_test_step1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    raise SystemExit(1 if any(r == "FAIL" for _, r, _ in results) else 0)


if __name__ == "__main__":
    main()

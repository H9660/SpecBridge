"""Build the candidate ticket list for the SpecBridge golden dataset.

For each repo in config/repos.json this script:
  1. downloads the repo history (no file contents) into --workdir,
  2. pins the "before" snapshot: the last commit before the cutoff date,
  3. finds O3 tickets whose code changes were all made after the cutoff,
  4. records which files each ticket changed (the "true" affected code),
then fetches each ticket from the public OpenMRS Jira and writes:
  data/snapshots.json            repo -> pinned commit
  data/golden/candidates_v0.json  every usable ticket with its tags
  data/golden/candidates_v0.md    the same, readable

Usage:
  py -3.12 scripts/build_ticket_shortlist.py --workdir <folder outside OneDrive>
"""
import argparse
import collections
import datetime
import json
import pathlib
import re
import subprocess
import urllib.parse
import urllib.request

PROJECT = pathlib.Path(__file__).resolve().parent.parent
KEY_RE = re.compile(r"\bO3-\d+\b")
# Tickets that are housekeeping rather than user-visible behaviour.
CHORE_RE = re.compile(r"\b(bump|upgrade|dependenc\w*|refactor\w*|e2e|playwright|jest|lint\w*|ci|storybook|deps|release|translations?|typos?|monorepo|webpack|rspack|tooling)\b", re.I)
CODE_RE = re.compile(r"\.(tsx?|jsx?)$")
TEST_RE = re.compile(r"(\.test\.|\.spec\.|__tests__|/e2e/|__mocks__)")
JIRA_FIELDS = "summary,issuetype,status,created,resolutiondate,components,labels,description"


def git(*args, cwd=None):
    return subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=cwd, check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


def history_since(repo, url, since, workdir):
    path = workdir / repo
    if not path.exists():
        git("clone", "-q", "--filter=blob:none", "--no-checkout", f"--shallow-since={since}", url, str(path))
    return path


def commits(path):
    """Yield (sha, date, subject) newest first."""
    for line in git("log", "--format=%H|%cI|%s", "origin/HEAD", cwd=path).splitlines():
        sha, date, subject = line.split("|", 2)
        yield sha, date[:10], subject


def changed_files(path, sha):
    return [f for f in git("show", "--name-only", "--format=", sha, cwd=path).splitlines() if f]


def adf_to_text(node):
    """Flatten Jira's rich-text format into plain text."""
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join(adf_to_text(n) for n in node)
    kind = node.get("type")
    if kind == "text":
        return node.get("text", "")
    if kind == "hardBreak":
        return "\n"
    if kind in ("inlineCard", "blockCard"):
        return node.get("attrs", {}).get("url", "")
    inner = adf_to_text(node.get("content"))
    if kind in ("paragraph", "heading", "listItem", "codeBlock", "blockquote", "tableRow"):
        return inner + "\n"
    if kind in ("tableCell", "tableHeader"):
        return inner + " | "
    return inner


def fetch_tickets(base_url, keys):
    tickets = {}
    for i in range(0, len(keys), 50):
        query = urllib.parse.urlencode({"jql": f"key in ({','.join(keys[i:i + 50])})",
                                        "fields": JIRA_FIELDS, "maxResults": 100})
        with urllib.request.urlopen(f"{base_url}/rest/api/3/search/jql?{query}", timeout=60) as resp:
            for issue in json.load(resp)["issues"]:
                f = issue["fields"]
                tickets[issue["key"]] = {
                    "key": issue["key"],
                    "url": f"{base_url}/browse/{issue['key']}",
                    "summary": f["summary"],
                    "type": f["issuetype"]["name"],
                    "status": f["status"]["name"],
                    "created": f["created"][:10],
                    "resolved": (f.get("resolutiondate") or "")[:10],
                    "components": [c["name"] for c in f.get("components") or []],
                    "labels": f.get("labels") or [],
                    "description": adf_to_text(f.get("description")).strip(),
                }
    return tickets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True, type=pathlib.Path,
                        help="where repo histories are downloaded (keep it outside OneDrive)")
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)

    config = json.loads((PROJECT / "config" / "repos.json").read_text(encoding="utf-8"))
    cutoff = config["cutoff"]
    # Look back one extra month so we can spot tickets that were already started before the cutoff.
    lookback = (datetime.date.fromisoformat(cutoff) - datetime.timedelta(days=31)).isoformat()

    snapshots = {}
    work = collections.defaultdict(lambda: {"repos": set(), "files": collections.defaultdict(set),
                                            "commits": [], "started_before_cutoff": False})
    for repo in config["repos"]:
        name = repo["name"]
        path = history_since(name, repo["url"], lookback, args.workdir)
        snapshot = git("rev-list", "-1", f"--before={cutoff}T00:00:00Z", "origin/HEAD", cwd=path).strip()
        snapshots[name] = {"url": repo["url"], "commit": snapshot,
                           "date": git("log", "-1", "--format=%cs", snapshot, cwd=path).strip()}
        for sha, date, subject in commits(path):
            for key in set(KEY_RE.findall(subject)):
                if date < cutoff:
                    work[key]["started_before_cutoff"] = True
                    continue
                work[key]["repos"].add(name)
                work[key]["files"][name].update(changed_files(path, sha))
                work[key]["commits"].append({"repo": name, "sha": sha, "date": date, "subject": subject})

    tickets = fetch_tickets(config["jira"]["base_url"], sorted(work))
    candidates, dropped = [], collections.Counter()
    for key, w in sorted(work.items(), key=lambda kv: int(kv[0].split("-")[1])):
        t = tickets.get(key)
        code = {r: sorted(f for f in files if CODE_RE.search(f) and not TEST_RE.search(f))
                for r, files in w["files"].items()}
        code = {r: files for r, files in code.items() if files}
        reason = (
            "not in Jira" if not t else
            "started before cutoff" if w["started_before_cutoff"] else
            "not finished" if t["status"] != "Done" else
            "epic/test ticket" if t["type"] in ("Epic", "Test") else
            "housekeeping" if CHORE_RE.search(t["summary"]) else
            "description too short" if len(t["description"]) < 80 else
            "no app code changed" if not code else
            None
        )
        if reason:
            dropped[reason] += 1
            continue
        text = t["description"].lower()
        tags = []
        if len(code) > 1:
            tags.append("cross-repo")
        tags.append("bug" if t["type"] == "Bug" else "feature")
        if "acceptance" in text:
            tags.append("has-acceptance-criteria")
        if len(t["description"]) < 250:
            tags.append("vague")
        candidates.append({**t, "tags": tags, "repos": sorted(code),
                           "changed_code_files": code, "commits": w["commits"]})

    golden = PROJECT / "data" / "golden"
    golden.mkdir(parents=True, exist_ok=True)
    (PROJECT / "data" / "snapshots.json").write_text(
        json.dumps({"cutoff": cutoff, "repos": snapshots}, indent=2), encoding="utf-8")
    (golden / "candidates_v0.json").write_text(json.dumps(candidates, indent=1), encoding="utf-8")
    write_markdown(golden / "candidates_v0.md", candidates, cutoff, dropped)

    print(f"tickets found in commits: {len(work)}  usable: {len(candidates)}")
    print("dropped:", dict(dropped))
    print("tags:", dict(collections.Counter(tag for c in candidates for tag in c["tags"])))
    print("repos:", dict(collections.Counter(r for c in candidates for r in c["repos"])))


def write_markdown(path, candidates, cutoff, dropped):
    lines = [
        "# Golden dataset candidates (v0)",
        "",
        f"Real O3 tickets whose code was changed only after **{cutoff}**. The repos are pinned to their last",
        "commit before that date (see `data/snapshots.json`), so for every ticket below the code SpecBridge",
        "reads is the code *before* the ticket was built - exactly what a PM would have at ticket creation.",
        "",
        f"Dropped: {', '.join(f'{n} {r}' for r, n in dropped.most_common())}.",
        "",
        "| # | Ticket | Type | Tags | Repos | Files changed | Summary |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, c in enumerate(candidates, 1):
        n_files = sum(len(f) for f in c["changed_code_files"].values())
        summary = c["summary"].replace("|", "\\|")
        lines.append(f"| {i} | [{c['key']}]({c['url']}) | {c['type']} | {', '.join(c['tags'])} | "
                     f"{', '.join(c['repos'])} | {n_files} | {summary} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

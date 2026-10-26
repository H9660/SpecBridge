"""Copy the shortlisted O3 tickets into the team's own Jira project.

The copy keeps the original summary and description (with formatting), but removes things
that would give away the answer or cannot work on another site:
  - links to GitHub pull requests and "PR #123" references (they point at the fix)
  - links back to OpenMRS Jira tickets (their comments discuss the fix); the link text stays
  - images / attachments and @mentions of OpenMRS people
The copy does NOT link back to the original ticket (its comments discuss the fix). The mapping
original -> copy is kept in data/golden/jira_import_map.json for the team.

Usage:
  py -3.12 scripts/import_tickets.py --dry-run   # build and check payloads, write a preview, no login needed
  py -3.12 scripts/import_tickets.py             # create the issues (needs .env); safe to re-run
"""
import argparse
import copy
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from atlassian import Atlassian, load_env, missing_settings  # noqa: E402

PROJECT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = PROJECT / "data" / "golden"
SOURCE_JIRA = "https://openmrs.atlassian.net"
LABEL = "golden-v0"
PR_URL_RE = re.compile(r"https?://github\.com/[^\s)]+/pull/\d+\S*", re.I)
PR_TEXT_RE = re.compile(r"\bPRs?\s*#\s*\d+", re.I)
FILE_RE = re.compile(r"[\w\-/]+\.(?:tsx?|jsx?|scss)\b")
DROP_NODES = {"media", "mediaSingle", "mediaGroup", "mediaInline"}


def fetch_source(keys):
    """Original summary, type and rich-text description from the public OpenMRS Jira."""
    out = {}
    for i in range(0, len(keys), 50):
        query = urllib.parse.urlencode({"jql": f"key in ({','.join(keys[i:i + 50])})",
                                        "fields": "summary,issuetype,description", "maxResults": 100})
        with urllib.request.urlopen(f"{SOURCE_JIRA}/rest/api/3/search/jql?{query}", timeout=60) as resp:
            for issue in json.load(resp)["issues"]:
                out[issue["key"]] = issue["fields"]
    return out


def clean(node, removed):
    """Return a sanitised copy of a Jira rich-text node (or None to drop it)."""
    if isinstance(node, list):
        return [c for c in (clean(n, removed) for n in node) if c is not None]
    kind = node.get("type")
    if kind in DROP_NODES:
        removed["attachments"] += 1
        return None
    if kind == "mention":
        removed["mentions"] += 1
        return {"type": "text", "text": "(someone)"}
    if kind in ("inlineCard", "blockCard"):
        url = node.get("attrs", {}).get("url", "")
        if PR_URL_RE.search(url):
            removed["pr_links"] += 1
        elif url.startswith(SOURCE_JIRA):
            removed["source_links"] += 1
        else:
            return node
        return {"type": "text", "text": "[link removed]"} if kind == "inlineCard" else None
    node = copy.copy(node)
    if kind == "text":
        marks = node.get("marks") or []
        for m in marks:
            href = m.get("attrs", {}).get("href", "") if m.get("type") == "link" else ""
            if PR_URL_RE.search(href):
                removed["pr_links"] += 1
            elif href.startswith(SOURCE_JIRA):
                removed["source_links"] += 1
            else:
                continue
            node["marks"] = [x for x in marks if x is not m]
        text, n = PR_URL_RE.subn("[link removed]", node.get("text", ""))
        removed["pr_links"] += n
        node["text"] = text
        return node if text else None
    if "content" in node:
        node["content"] = scrub_pr_text(merge_text(clean(node["content"], removed)), removed)
    return node


def merge_text(nodes):
    """Join neighbouring text nodes with the same formatting, so "PR " + "#2551" can be matched."""
    out = []
    for n in nodes:
        if out and n.get("type") == "text" and out[-1].get("type") == "text" \
                and (n.get("marks") or []) == (out[-1].get("marks") or []):
            out[-1] = {**out[-1], "text": out[-1]["text"] + n["text"]}
        else:
            out.append(n)
    return out


def scrub_pr_text(nodes, removed):
    for n in nodes:
        if n.get("type") == "text":
            n["text"], count = PR_TEXT_RE.subn("[PR reference removed]", n["text"])
            removed["pr_links"] += count
    return nodes


def adf_text(node):
    if isinstance(node, list):
        return " ".join(adf_text(n) for n in node)
    return node.get("text", "") + " " + adf_text(node.get("content", []))


def build_payloads(picked, source):
    payloads, report = [], []
    for p in picked:
        src = source[p["key"]]
        removed = {"pr_links": 0, "source_links": 0, "attachments": 0, "mentions": 0}
        desc = clean(src["description"], removed) if src.get("description") else \
            {"type": "doc", "version": 1, "content": []}
        text = adf_text(desc)
        flags = []
        if FILE_RE.search(text) or FILE_RE.search(src["summary"]):
            flags.append("mentions-files")
        payloads.append({"source": p["key"], "group": p["group"], "summary": src["summary"],
                         "source_type": src["issuetype"]["name"], "description": desc})
        report.append({"source": p["key"], **removed, "flags": flags,
                       "leftover_pr_refs": len(PR_URL_RE.findall(text)) + len(PR_TEXT_RE.findall(text))})
    return payloads, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    picked = json.loads((GOLDEN / "picked_v0.json").read_text(encoding="utf-8"))["picked"]
    source = fetch_source([p["key"] for p in picked])
    payloads, report = build_payloads(picked, source)
    (GOLDEN / "jira_import_preview.json").write_text(json.dumps(
        {"report": report, "payloads": payloads}, indent=1), encoding="utf-8")
    totals = {k: sum(r[k] for r in report)
              for k in ("pr_links", "source_links", "attachments", "mentions", "leftover_pr_refs")}
    print(f"prepared {len(payloads)} tickets; removed {totals}; "
          f"mentions-files: {sum('mentions-files' in r['flags'] for r in report)}")
    if args.dry_run:
        print("dry run - preview written to data/golden/jira_import_preview.json")
        return

    env = load_env()
    if missing_settings(env):
        raise SystemExit(f".env is missing: {', '.join(missing_settings(env))} (copy .env.example to .env)")
    site = Atlassian(env)
    types = site.issue_types()
    fallback = next((t for t in ("Story", "Task") if t in types), None)
    if not fallback:
        raise SystemExit(f"project {site.project} has no Story or Task issue type: {sorted(types)}")

    map_path = GOLDEN / "jira_import_map.json"
    mapping = json.loads(map_path.read_text(encoding="utf-8")) if map_path.exists() else {}
    existing = {i["fields"]["summary"]: i["key"] for i in site.search(f'project = {site.project} AND labels = "{LABEL}"')}
    created = 0
    for p, r in zip(payloads, report):
        if p["summary"] in existing:
            mapping[p["source"]] = existing[p["summary"]]
            continue
        type_name = "Bug" if p["source_type"] == "Bug" and "Bug" in types else fallback
        result = site.create_issue({
            "project": {"key": site.project},
            "issuetype": {"id": types[type_name]},
            "summary": p["summary"],
            "description": p["description"],
            "labels": [LABEL, *r["flags"]],
        })
        mapping[p["source"]] = result["key"]
        map_path.write_text(json.dumps(mapping, indent=1), encoding="utf-8")
        created += 1
        print(f"  {p['source']} -> {result['key']}")
    map_path.write_text(json.dumps(mapping, indent=1), encoding="utf-8")
    print(f"created {created}, already there {len(payloads) - created}")


if __name__ == "__main__":
    main()

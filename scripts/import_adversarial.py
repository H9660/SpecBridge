"""Add a hand-written ticket set (default data/golden/adversarial_v0.json) to the team's Jira project.

Labels: the set's label (e.g. `adversarial-v0`, `edge-v1`) plus `trick-<type>`. Safe to re-run: a ticket whose
summary already exists with the label is not created again. Writes the id -> SPEC key map next to the set
(adversarial_import_map.json for the trick tickets, <set>_import_map.json otherwise).

Usage:
  py -3.12 scripts/import_adversarial.py [--dry-run]
  py -3.12 scripts/import_adversarial.py --file test_tickets_v1.json [--dry-run]     # the edge-case tickets
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge.atlassian import Atlassian, missing_settings  # noqa: E402
from specbridge.env import load_env  # noqa: E402

PROJECT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = PROJECT / "data" / "golden"


def to_adf(text):
    """Plain text -> Jira rich text: blank lines split paragraphs, single newlines become line breaks."""
    paragraphs = []
    for block in text.split("\n\n"):
        content = []
        for i, line in enumerate(block.split("\n")):
            if i:
                content.append({"type": "hardBreak"})
            if line:
                content.append({"type": "text", "text": line})
        paragraphs.append({"type": "paragraph", "content": content})
    return {"type": "doc", "version": 1, "content": paragraphs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--file", default="adversarial_v0.json", help="a ticket set in data/golden/")
    args = parser.parse_args()

    source = GOLDEN / pathlib.Path(args.file).name
    data = json.loads(source.read_text(encoding="utf-8"))
    label = data["label"]
    payloads = [{"id": t["id"], "summary": t["summary"], "type": t["issue_type"],
                 "labels": [label, f"trick-{t['trick']}"],
                 "description": to_adf(t["description"]) if t["description"].strip() else None}
                for t in data["tickets"]]
    if args.dry_run:
        for p in payloads:
            size = len(json.dumps(p["description"])) if p["description"] else 0
            print(p["id"], p["type"], p["labels"], p["summary"], f"(description {size:,} characters as Jira JSON)")
        return

    env = load_env()
    if missing_settings(env):
        raise SystemExit(f".env is missing: {', '.join(missing_settings(env))}")
    site = Atlassian(env)
    types = site.issue_types()
    existing = {i["fields"]["summary"]: i["key"] for i in site.search(f'project = {site.project} AND labels = "{label}"')}
    map_path = GOLDEN / ("adversarial_import_map.json" if source.name == "adversarial_v0.json"
                         else f"{source.stem}_import_map.json")
    mapping = json.loads(map_path.read_text(encoding="utf-8")) if map_path.exists() else {}
    created = 0
    for p in payloads:
        if p["summary"] in existing:
            mapping[p["id"]] = existing[p["summary"]]
            continue
        type_name = p["type"] if p["type"] in types else "Task"
        fields = {"project": {"key": site.project}, "issuetype": {"id": types[type_name]},
                  "summary": p["summary"], "labels": p["labels"]}
        if p["description"]:
            fields["description"] = p["description"]
        result = site.create_issue(fields)
        mapping[p["id"]] = result["key"]
        map_path.write_text(json.dumps(mapping, indent=1), encoding="utf-8")
        created += 1
        print(f"  {p['id']} -> {result['key']} ({type_name})")
    map_path.write_text(json.dumps(mapping, indent=1), encoding="utf-8")
    print(f"created {created}, already there {len(payloads) - created}")


if __name__ == "__main__":
    main()

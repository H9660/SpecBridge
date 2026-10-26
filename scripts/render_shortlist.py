"""Turn data/golden/picked_v0.json into a readable shortlist (data/golden/shortlist_v0.md)."""
import collections
import json
import pathlib

PROJECT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = PROJECT / "data" / "golden"


def main():
    picked = json.loads((GOLDEN / "picked_v0.json").read_text(encoding="utf-8"))
    candidates = {c["key"]: c for c in json.loads((GOLDEN / "candidates_v0.json").read_text(encoding="utf-8"))}
    missing = [p["key"] for p in picked["picked"] if p["key"] not in candidates]
    if missing:
        raise SystemExit(f"picked tickets not in candidates_v0.json: {missing}")

    by_group = collections.defaultdict(list)
    for p in picked["picked"]:
        by_group[p["group"]].append(candidates[p["key"]])

    lines = ["# Golden dataset shortlist (v0)", "", picked["note"], "",
             f"**{len(picked['picked'])} real tickets** + {len(picked['to_write_by_hand'])} hand-written tricky tickets.", ""]
    for group, why in picked["groups"].items():
        tickets = by_group.get(group, [])
        lines += [f"## {group} ({len(tickets)})", "", why, "",
                  "| Ticket | Type | Repos | Code files changed | Summary |", "|---|---|---|---|---|"]
        for c in tickets:
            n_files = sum(len(f) for f in c["changed_code_files"].values())
            summary = c["summary"].replace("|", "\\|")
            lines.append(f"| [{c['key']}]({c['url']}) | {c['type']} | {', '.join(c['repos'])} | {n_files} | {summary} |")
        lines.append("")
    lines += ["## To write by hand (adversarial)", ""] + [f"- {t}" for t in picked["to_write_by_hand"]]
    (GOLDEN / "shortlist_v0.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({g: len(t) for g, t in by_group.items()})


if __name__ == "__main__":
    main()

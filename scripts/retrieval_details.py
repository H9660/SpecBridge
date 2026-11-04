"""Per-ticket evidence behind the Step 4 search scores.

For every golden ticket: its title, the files the real fix changed (the targets), and the top 20
files returned by combined search (no embeddings) and hybrid search (with embeddings), with the
targets marked. Writes data/retrieval/details.md (readable) and details.json (every list).

Usage:
  py -3.12 scripts/retrieval_details.py [--workdir C:/specbridge-work]
"""
import argparse
import json
import pathlib
import sys

PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from specbridge.code_index import CodeIndex  # noqa: E402
from specbridge.embedder import load_embedder  # noqa: E402
from specbridge.env import load_env  # noqa: E402
from specbridge.retrieval_eval import golden_queries  # noqa: E402

OUT = PROJECT / "data" / "retrieval"
K = 20


def rank_of(target, found):
    return found.index(target) + 1 if target in found else None


def fmt_rank(r):
    return str(r) if r else "-"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir")
    args = parser.parse_args()
    workdir = pathlib.Path(args.workdir or load_env()["SPECBRIDGE_WORKDIR"])

    index = CodeIndex(workdir)
    index.build()
    embedder = load_embedder()
    titles = {p["source"]: p["summary"] for p in json.loads(
        (PROJECT / "data" / "golden" / "jira_import_preview.json").read_text(encoding="utf-8"))["payloads"]}

    tickets = []
    for q in golden_queries(workdir):
        combined = [tuple(f) for f in index.rank_files(q.text, K)]
        hybrid = [tuple(f) for f in index.rank_files(q.text, K, embedder)]
        targets = sorted(q.targets)
        tickets.append({
            "key": q.key, "spec_key": q.spec_key, "group": q.group, "mentions_files": q.mentions_files,
            "title": titles.get(q.key, ""), "missing_targets": q.missing,
            "targets": [{"file": f"{r}/{p}", "rank_combined": rank_of((r, p), combined),
                         "rank_hybrid": rank_of((r, p), hybrid)} for r, p in targets],
            "combined_top20": [f"{r}/{p}" for r, p in combined],
            "hybrid_top20": [f"{r}/{p}" for r, p in hybrid],
        })
    index.close()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "details.json").write_text(json.dumps(tickets, indent=1), encoding="utf-8")

    lines = ["# Code search - per-ticket details", "",
             "For each golden ticket: the files the real fix changed (targets) and where each search put them, "
             "then the hybrid top 20 with targets marked **<- target**.",
             "Combined = keywords + links (no embeddings). Hybrid = keywords + meaning (nomic-embed-text) + links. "
             "Rank `-` = not in the top 20. `*` after the group = ticket names code files.", "",
             "## Summary", "",
             "| Ticket | Group | Title | Targets | Best rank combined | Best rank hybrid |", "|---|---|---|---|---|---|"]
    for t in tickets:
        best = lambda col: min((x[col] for x in t["targets"] if x[col]), default=None)  # noqa: E731
        star = " *" if t["mentions_files"] else ""
        lines.append(f"| {t['spec_key']} ({t['key']}) | {t['group']}{star} | {t['title'][:70]} | "
                     f"{len(t['targets'])} | {fmt_rank(best('rank_combined'))} | {fmt_rank(best('rank_hybrid'))} |")
    for t in tickets:
        star = " (names code files)" if t["mentions_files"] else ""
        lines += ["", f"## {t['spec_key']} ({t['key']}) - {t['group']}{star}", "", f"**{t['title']}**", ""]
        if not t["targets"]:
            lines.append(f"Not scored: none of the changed files existed at the frozen version "
                         f"({t['missing_targets']} skipped).")
            continue
        lines += ["| Changed file (target) | Rank combined | Rank hybrid |", "|---|---|---|"]
        lines += [f"| `{x['file']}` | {fmt_rank(x['rank_combined'])} | {fmt_rank(x['rank_hybrid'])} |"
                  for x in t["targets"]]
        if t["missing_targets"]:
            lines.append(f"\n({t['missing_targets']} other changed files were tests or did not exist yet; not counted.)")
        target_set = {x["file"] for x in t["targets"]}
        lines += ["", "Hybrid top 20:", ""]
        lines += [f"{i}. `{f}`{' **<- target**' if f in target_set else ''}"
                  for i, f in enumerate(t["hybrid_top20"], 1)]
    (OUT / "details.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(tickets)} tickets -> data/retrieval/details.md and details.json")


if __name__ == "__main__":
    main()

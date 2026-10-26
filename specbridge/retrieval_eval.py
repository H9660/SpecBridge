"""Score code search on the golden tickets: do the files that were really changed come back near the top?

Query  = the cleaned ticket text that was copied into Jira (summary + description, no PR links).
Target = the files the real fix changed, counting only non-test code files that already existed
         at the frozen version (files the fix created cannot be found).
Any search method can be scored: it is a function (ticket text, k) -> list of (repo, path), best first.
"""
import json
import subprocess
from dataclasses import dataclass, field

from specbridge.code_index import TEST_FILE
from specbridge.env import PROJECT

GOLDEN = PROJECT / "data" / "golden"
KS = (5, 10, 20)


@dataclass
class GoldenQuery:
    key: str          # original O3 key
    spec_key: str     # copy in the team Jira
    group: str
    mentions_files: bool
    text: str
    targets: set = field(default_factory=set)   # {(repo, path)}
    missing: int = 0  # changed files that did not exist at the frozen version, or were tests


def adf_text(node):
    """Plain text of a Jira rich-text description."""
    if isinstance(node, list):
        return " ".join(adf_text(n) for n in node)
    return node.get("text", "") + " " + adf_text(node.get("content", []))


def golden_queries(workdir):
    preview = json.loads((GOLDEN / "jira_import_preview.json").read_text(encoding="utf-8"))
    flags = {r["source"]: r["flags"] for r in preview["report"]}
    changed = {c["key"]: c["changed_code_files"]
               for c in json.loads((GOLDEN / "candidates_v0.json").read_text(encoding="utf-8"))}
    spec = json.loads((GOLDEN / "jira_import_map.json").read_text(encoding="utf-8"))
    queries = []
    for p in preview["payloads"]:
        q = GoldenQuery(p["source"], spec.get(p["source"], "?"), p["group"], "mentions-files" in flags[p["source"]],
                        f"{p['summary']}\n\n{adf_text(p['description'])}")
        for repo, files in changed[p["source"]].items():
            for path in files:
                exists = subprocess.run(["git", "-C", str(workdir / repo), "cat-file", "-e", f"snapshot:{path}"],
                                        capture_output=True).returncode == 0
                if exists and not TEST_FILE.search(path):
                    q.targets.add((repo, path))
                else:
                    q.missing += 1
        queries.append(q)
    return queries


def score(search, queries, ks=KS):
    """Per-ticket results. Tickets with no findable target are kept but marked unscored."""
    rows = []
    for q in queries:
        found = [tuple(h) for h in search(q.text, max(ks))]
        ranks = sorted(found.index(t) + 1 for t in q.targets if t in found)
        row = {"key": q.key, "spec_key": q.spec_key, "group": q.group, "mentions_files": q.mentions_files,
               "targets": len(q.targets), "missing": q.missing, "scored": bool(q.targets),
               "first_rank": ranks[0] if ranks else None, "top": [f"{r}/{p}" for r, p in found[:5]]}
        for k in ks:
            hits = sum(r <= k for r in ranks)
            row[f"hit@{k}"] = hits > 0
            row[f"recall@{k}"] = hits / len(q.targets) if q.targets else None
        row["rr"] = 1 / ranks[0] if ranks else 0.0
        rows.append(row)
    return rows


def summarise(rows, ks=KS):
    """Averages over scored tickets: overall, per group, and with / without file names in the ticket."""
    def avg(sel):
        sel = [r for r in sel if r["scored"]]
        if not sel:
            return None
        out = {"tickets": len(sel), "mrr": sum(r["rr"] for r in sel) / len(sel)}
        for k in ks:
            out[f"hit@{k}"] = sum(r[f"hit@{k}"] for r in sel) / len(sel)
            out[f"recall@{k}"] = sum(r[f"recall@{k}"] for r in sel) / len(sel)
        return out
    groups = {"all": rows,
              "no file names in ticket": [r for r in rows if not r["mentions_files"]],
              "file names in ticket (mentions-files)": [r for r in rows if r["mentions_files"]]}
    for g in sorted({r["group"] for r in rows}):
        groups[f"group: {g}"] = [r for r in rows if r["group"] == g]
    return {name: avg(sel) for name, sel in groups.items()}


def report_md(method, rows, summary, ks=KS, extra=()):
    cols = ["tickets", *[f"hit@{k}" for k in ks], *[f"recall@{k}" for k in ks], "mrr"]
    lines = [f"# Code search scores - method: {method}", "", *extra, "",
             "hit@k = share of tickets with at least one really-changed file in the top k; "
             "recall@k = share of each ticket's changed files found in the top k (averaged); "
             "mrr = average of 1 / rank of the first changed file found.", "",
             "| Tickets | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for name, s in summary.items():
        if s:
            lines.append(f"| {name} | " + " | ".join(
                str(s[c]) if c == "tickets" else f"{s[c]:.2f}" for c in cols) + " |")
    unscored = [r["key"] for r in rows if not r["scored"]]
    lines += ["", f"Not scored (no changed file existed at the frozen version): {', '.join(unscored) or 'none'}", "",
              "## Per ticket", "", "| Ticket | Group | Files | First found at | Top result |", "|---|---|---|---|---|"]
    for r in rows:
        first = r["first_rank"] or ("-" if r["scored"] else "n/a")
        lines.append(f"| {r['spec_key']} ({r['key']}) | {r['group']}{' *' if r['mentions_files'] else ''} | "
                     f"{r['targets']} | {first} | {r['top'][0] if r['top'] else '-'} |")
    lines += ["", "\\* ticket names code files (scored separately)."]
    return "\n".join(lines) + "\n"

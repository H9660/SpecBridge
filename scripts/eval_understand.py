"""Score the understand node on all SPEC tickets (real AI calls: about $0.005 at list price, $0 on the free tier, and 10-25 s per ticket).

Expected: the 63 real tickets (SPEC-1..63, fixed by OpenMRS developers) are testable, fit the product and
have no unknown screen to change; the 6 trick tickets (SPEC-64..69) match data/golden/adversarial_v0.json;
the hand-written off-domain tickets (data/golden/off_domain_v0.json) match their expected domain fit.
Writes data/understand/<prompt version>.md and .json (scores), and data/understand/<prompt version>/<ticket>.json
(understand's full answer for each ticket).

Usage:
  .venv/bin/python scripts/eval_understand.py                 # everything (about 6 minutes with 4 at a time)
  .venv/bin/python scripts/eval_understand.py --keys SPEC-12 SPEC-46
"""
import argparse
import json
import pathlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge.agent.nodes import intake, understand  # noqa: E402
from specbridge.env import PROJECT  # noqa: E402

GOLDEN = PROJECT / "data" / "golden"
OUT = PROJECT / "data" / "understand"
OUT_OF_CREDIT = threading.Event()   # set on the first HTTP 402: stop calling the AI


def expectations():
    adv = {t["id"]: t["expected"] for t in json.loads((GOLDEN / "adversarial_v0.json").read_text())["tickets"]}
    spec_of = json.loads((GOLDEN / "adversarial_import_map.json").read_text())
    exp = {f"SPEC-{n}": {"testable": True, "domain_fit": "fits", "risks": [], "group": "real"} for n in range(1, 64)}
    for adv_id, key in spec_of.items():
        exp[key] = {**adv[adv_id], "group": f"trick ({adv_id})"}
    for t in json.loads((GOLDEN / "off_domain_v0.json").read_text())["tickets"]:
        exp[t["id"]] = {**t["expected"], "group": "off-domain", "ticket": t}
    return exp


def judge(und, e):
    problems = []
    if und["testable"] is not e["testable"]:
        problems.append(f"testable {und['testable']} (expected {e['testable']}): {und['reason']}")
    if e.get("domain_fit") and und["domain_fit"] != e["domain_fit"]:
        problems.append(f"domain {und['domain_fit']} (expected {e['domain_fit']})")
    if e.get("domain_fit_not") and und["domain_fit"] == e["domain_fit_not"]:
        problems.append(f"domain {und['domain_fit']}")
    kinds = {r["kind"] for r in und["risks"]}
    problems += [f"missing risk {r}" for r in e.get("risks", []) if r not in kinds]
    problems += [f"unexpected risk {r}" for r in e.get("risks_not", []) if r in kinds]
    if e["group"] == "real" and "unknown-screen" in kinds:
        problems.append("unknown-screen on a real ticket: " +
                        ", ".join(s["name"] for s in und["screens"] if s["found_in_code"] is False))
    return problems


def run_one(key, e):
    t0 = time.time()
    if OUT_OF_CREDIT.is_set():
        return {"key": key, "group": e["group"], "ok": False, "problems": ["skipped: no credit or quota left"], "seconds": 0.0}
    try:
        if "ticket" in e:
            od = e["ticket"]
            ticket = {"key": "SPEC-999", "type": od["type"], "title": od["title"], "text": od["text"], "labels": [], "flags": []}
        else:
            ticket = intake.node({"ticket_ref": key}, None)["ticket"]
        und = understand.node({"ticket": ticket}, None)["understanding"]
    except Exception as err:  # noqa: BLE001 - one failing ticket is reported, the rest still run
        if "no credit or quota left" in str(err):
            OUT_OF_CREDIT.set()
        return {"key": key, "group": e["group"], "ok": False, "problems": [f"{type(err).__name__}: {err}"],
                "seconds": round(time.time() - t0, 1)}
    problems = judge(und, e)
    answers = OUT / und["meta"]["prompt_version"].split(" ")[0]
    answers.mkdir(parents=True, exist_ok=True)
    (answers / f"{key}.json").write_text(json.dumps({"ticket": ticket, "understanding": und}, indent=1,
                                                    ensure_ascii=False), encoding="utf-8")
    c = und["criteria"]
    return {"key": key, "group": e["group"], "ok": not problems, "problems": problems, "testable": und["testable"],
            "domain_fit": und["domain_fit"], "criteria": len(c), "stated": sum(x["source"] == "stated" for x in c),
            "inferred": sum(x["source"] == "inferred" for x in c), "questions": len(und["questions"]),
            "risks": [r["kind"] for r in und["risks"]],
            "unknown_screens": [s["name"] for s in und["screens"] if s["found_in_code"] is False],
            "cost": und["meta"]["cost_usd"], "seconds": round(time.time() - t0, 1),
            "prompt_version": und["meta"]["prompt_version"], "model": und["meta"]["model"]}


def report(rows):
    version = next((r["prompt_version"] for r in rows if r.get("prompt_version")), "unknown")
    lines = [f"# understand on the SPEC tickets - prompt {version}", "",
             f"Run {time.strftime('%Y-%m-%d %H:%M')}; model {next((r['model'] for r in rows if r.get('model')), '?')}.", "",
             "| Group | Tickets | As expected |", "|---|---|---|"]
    for g in ("real", "trick", "off-domain"):
        sel = [r for r in rows if r["group"].startswith(g)]
        if sel:
            lines.append(f"| {g} | {len(sel)} | {sum(r['ok'] for r in sel)} |")
    cost = sum(r.get("cost") or 0 for r in rows)
    secs = [r["seconds"] for r in rows]
    lines += ["", f"Total cost ${cost:.3f}; time per ticket {min(secs)}-{max(secs)} s "
                  f"(median {sorted(secs)[len(secs) // 2]} s).", "",
              "| Ticket | Group | OK | Testable | Domain | Criteria (stated / inferred) | Questions | Risks | Problems |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        crit = f"{r['criteria']} ({r['stated']} / {r['inferred']})" if "criteria" in r else "-"
        lines.append(f"| {r['key']} | {r['group']} | {'yes' if r['ok'] else '**no**'} | {r.get('testable', '-')} | "
                     f"{r.get('domain_fit', '-')} | {crit} | {r.get('questions', '-')} | "
                     f"{', '.join(r.get('risks', [])) or '-'} | {'; '.join(r['problems']) or '-'} |")
    return version, "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keys", nargs="*")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    exp = expectations()
    keys = args.keys or list(exp)
    with ThreadPoolExecutor(args.workers) as pool:
        rows = list(pool.map(lambda k: run_one(k, exp[k]), keys))
    for r in rows:
        print(f"{r['key']:9} {'ok ' if r['ok'] else 'BAD'} {'; '.join(r['problems'])}")
    if OUT_OF_CREDIT.is_set():
        print("\nStopped: the AI provider has no credit or quota left. No report written; the answers so far are "
              f"in {OUT}. Wait (free-tier limits reset) or turn on billing, and run again.")
        return 1
    version, md = report(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    name = version.split(" ")[0]
    (OUT / f"{name}.md").write_text(md, encoding="utf-8")
    (OUT / f"{name}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\n{sum(r['ok'] for r in rows)}/{len(rows)} as expected -> {OUT / name}.md")


if __name__ == "__main__":
    sys.exit(main())

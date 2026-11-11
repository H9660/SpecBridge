"""Run SpecBridge on one ticket (the START of the agent graph).

Usage:
  .venv/bin/python scripts/run_ticket.py SPEC-12
  .venv/bin/python scripts/run_ticket.py https://rooks101.atlassian.net/browse/SPEC-12 --mode eval
  .venv/bin/python scripts/run_ticket.py --resume --run-id 20261107-101500-a1b2c3
Options: --mode dry-run (default) | eval | live  (live publishes the page to Confluence and comments on the ticket);  --no-preflight skips the
online brain check (offline work and tests);  --records-dir puts run records somewhere else.
Exit codes: 0 done, 1 the run failed, 2 refused before starting, 130 stopped with Ctrl-C.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge.agent import run_record  # noqa: E402
from specbridge.agent.graph import StartError, new_run_id, run_ticket  # noqa: E402
from specbridge.agent.limits import SettingsError  # noqa: E402
from specbridge.agent.nodes.intake import IntakeError  # noqa: E402
from specbridge.agent.preflight import PreflightError  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run SpecBridge on one Jira ticket.")
    parser.add_argument("ticket", nargs="?", help="ticket URL or key, e.g. SPEC-12")
    parser.add_argument("--mode", default="dry-run")
    parser.add_argument("--run-id")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--no-preflight", action="store_true")
    parser.add_argument("--records-dir", type=pathlib.Path, default=run_record.RUNS)
    args = parser.parse_args(argv)

    run_id = args.run_id or (None if args.resume else new_run_id())
    try:
        result = run_ticket(args.ticket, args.mode, run_id, args.resume, not args.no_preflight,
                            records_dir=args.records_dir)
    except (StartError, SettingsError, PreflightError) as err:
        print(f"refused: {err}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(f"\nstopped. Continue with: --resume --run-id {run_id}", file=sys.stderr)
        return 130
    except IntakeError as err:
        hint = f"; continue with --resume --run-id {run_id}" if err.retryable else ""
        print(f"intake: {err}\nRun {run_id} ended with status error (record in {args.records_dir}){hint}",
              file=sys.stderr)
        return 1
    except Exception as err:  # noqa: BLE001 - the record is already written; show it and exit
        print(f"run {run_id} failed: {type(err).__name__}: {err}\n"
              f"Record in {args.records_dir}; continue with --resume --run-id {run_id}", file=sys.stderr)
        return 1

    if result.brain:
        b = result.brain
        print(f"brain:  {b['brain']} ({b['provider']} {b['model']})" + ("" if b["network_checked"] else ", not checked online"))
        for w in b.get("warnings", []):
            print(f"warning: {w}")
    ticket = result.state.get("ticket")
    if ticket:
        print(f"ticket: {ticket['key']}  {ticket['type']}  \"{ticket['title'][:70]}\"  status: {ticket['status']}")
        print(f"text:   {len(ticket['text']):,} characters")
        flags = ticket["flags"]
        print("flags:  " + ("none" if not flags else "\n        ".join(f"{f['kind']}: {f['detail']}" for f in flags)))
    u = result.state.get("understanding")
    if u:
        crit = u["criteria"]
        print(f"intent: {u['intent']}")
        print(f"criteria: {len(crit)} ({sum(c['source'] == 'stated' for c in crit)} stated, "
              f"{sum(c['source'] == 'inferred' for c in crit)} inferred, "
              f"{sum(c['status'] != 'ok' for c in crit)} conflicting/unclear)")
        for c in crit:
            print(f"  {c['id']} [{c['source']}{'' if c['status'] == 'ok' else ', ' + c['status']}] {c['text']}")
        print("screens: " + (", ".join(f"{s['name']} ({s['role']}, "
                                         f"{'in code' if s['found_in_code'] else 'NOT in code' if s['found_in_code'] is False else 'unchecked'})"
                                         for s in u["screens"]) or "none"))
        print("risks:  " + (", ".join(r["kind"] for r in u["risks"]) or "none") + f"   domain: {u['domain_fit']}")
        for q in u["questions"]:
            print(f"  ? {q}")
        scope = {"full": "", "regression": " (regression check only)", "none": ""}.get(u.get("test_scope", ""), "")
        print(f"testable: {'yes' if u['testable'] else 'NO'}{scope} - {u['reason']}")
        m = u["meta"]
        cached = f" ({m['cached_input_tokens']} input from cache)" if m.get("cached_input_tokens") else ""
        print(f"AI:     {m['model']}, {m['input_tokens'] + m['output_tokens']} tokens{cached}, "
              f"{'~' if m.get('cost_estimated') else ''}${m['cost_usd']:.4f}, "
              f"{m['seconds']} s" + (", own key (BYOK)" if m.get("byok") else ""))
    c = result.state.get("clarification")
    if c:
        print(f"clarify: {c['category']} - {c['headline']}")
        for i, q in enumerate(c["questions"], 1):
            print(f"  {i}. {q}")
        print(f"  next step: {c['next_step']}")
        print("--- Jira comment (posted by publish, later) ---\n" + c["comment"] + "\n---")
    items = result.state.get("work_items")
    if items is not None and result.state.get("orchestration"):
        o = result.state["orchestration"]
        print(f"plan:   {len(items)} worker(s){' + e2e worker' if result.state.get('e2e') else ''}; search {o['search']}; "
              f"grouping by {o['ai'].get('used')}" + (f" ({o['ai']['why']})" if o["ai"].get("why") else ""))
        for it in items:
            print(f"  {it['id']} {', '.join(it['criterion_ids'])}: {it['slice']['focus'] or '-'}")
            print("     starts at: " + "; ".join(e["path"].split("/")[-1] + (" (shared)" if e["shared"] else "")
                                           for e in it["seed_evidence"][:4]))
        for s in result.state.get("skipped", []):
            print(f"  skipped {s['criterion_id']}: {s['reason']}")
        b = o["budget"]
        print(f"budget: ${b['remaining']:.4f} left of ${b['cap']}; ${b['per_worker']:.4f} per worker, "
              f"reserve ${b['reserve']:.4f}, {b['tool_calls']} tool calls each")
    for res in result.state.get("results") or []:
        m = res.get("meta", {})
        print(f"worker {res['work_item_id']} ({', '.join(res['criterion_ids'])}): {res['status']}"
              + (f" - {res['error']}" if res.get("error") else "")
              + (f"; {m.get('tool_calls')} tool calls, {res.get('evidence_read', 0)} pieces of code read, stop: {res.get('stop')}"
                 if m else ""))
        for case in res.get("cases", []):
            crit = "+".join(case.get("criterion_ids") or [case["criterion_id"]])
            print(f"  {case['id']} [{crit}, {case['type']}] {case['title']}  (cites {', '.join(case['evidence_ids'])})")
        for u in res.get("untestable", []):
            print(f"  untestable {u['criterion_id']}: {u['reason']}")
        if res["work_item_id"] == "E2E" and not res.get("cases") and res.get("missing"):
            print(f"  no flow: {res['missing']}")
        if res.get("uncovered"):
            print(f"  not covered: {', '.join(res['uncovered'])}")
        for d in res.get("dropped", []):
            print(f"  dropped: {d}")
    plan = result.state.get("plan")
    if plan:
        print(f"plan:   {len(plan['cases'])} test case(s), {len(plan['evidence'])} piece(s) of evidence; "
              f"editor: {plan['editor'].get('used')}" + (f" ({plan['editor']['why']})" if plan["editor"].get("why") else ""))
        for row in plan["criteria"]:
            print(f"  {row['id']} {row['status']}: {', '.join(row['cases']) or row['detail']}")
        for p in plan["common_preconditions"]:
            print(f"  common precondition: {p}")
        for case in plan["cases"]:
            print(f"  {case['id']} [{'+'.join(case['criterion_ids'])}, {case['type']}] {case['title']}  "
                  f"(cites {', '.join(case['evidence_ids'])}; from {case['source']})")
        for ch in plan["changes"]:
            print(f"  {'applied' if ch['applied'] else 'refused'}: {ch['change']}" + (f" - {ch['why']}" if ch["why"] else ""))
    review = result.state.get("review")
    if review:
        print(f"review: round {review['round']}; {review['scores']}"
              + (f"; retrying {', '.join(review['retry'])}" if review.get("retry") else "")
              + (f"; final: {review['final']['status']}" + (f" ({review['final']['reason']})" if review["final"]["reason"] else "")
                 if review.get("final") else ""))
        for cid, v in review["per_criterion"].items():
            print(f"  {cid} {v['verdict']}" + (f" - hint: {v['retry_hint']}" if v.get("retry_hint") else ""))
            for p in v.get("problems", []):
                print(f"     {p['kind']}{' ' + p['case'] if p['case'] else ''}: {p['detail']}")
        for case in (result.state.get("plan") or {}).get("cases", []):
            for f in case.get("flags", []):
                print(f"  flag {case['id']} {f['kind']}: {f['detail']}")
    page = result.state.get("page")
    if page:
        print(f"page:   {page['title']} ({page['summary']['kind']}, {len(page['storage']):,} characters)")
        print("comment:\n  " + page["comment"].replace("\n", "\n  "))
    published = result.state.get("published") or {}
    if published.get("page_url"):
        print(f"published: {published['page_url']}  (page {published['page_action']}, version "
              f"{published['page_version']}; Jira comment {published['comment_action'] or 'not written'})")
    if published.get("error"):
        print(f"published: NOT PUBLISHED - {published['error']}")
        if (published.get("fallback") or {}).get("files"):
            print(f"           saved locally instead: {published['fallback']['files']['html']}")
    saved = result.state.get("saved") or {}
    if saved.get("files"):
        print(f"saved:  {saved['files']['html']}  (open in a browser; also page.md, page.storage.xml, comment.txt)")
    for w in saved.get("warnings", []):
        print(f"  warning: {w}")
    if saved.get("error"):
        print(f"saved:  NOT SAVED - {saved['error']}")
    print(f"run:    {result.run_id}")
    print(f"status: {result.status}" + (f" ({result.message})" if result.message else ""))
    print(f"record: {result.record_path}")
    return 1 if saved.get("error") or published.get("error") else 0   # the page was not saved / published


if __name__ == "__main__":
    sys.exit(main())

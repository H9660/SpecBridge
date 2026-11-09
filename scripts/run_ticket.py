"""Run SpecBridge on one ticket (the START of the agent graph).

Usage:
  .venv/bin/python scripts/run_ticket.py SPEC-12
  .venv/bin/python scripts/run_ticket.py https://rooks101.atlassian.net/browse/SPEC-12 --mode eval
  .venv/bin/python scripts/run_ticket.py --resume --run-id 20261107-101500-a1b2c3
Options: --mode dry-run (default) | eval  (live waits for the publish node);  --no-preflight skips the
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
        print(f"testable: {'yes' if u['testable'] else 'NO'} - {u['reason']}")
        m = u["meta"]
        print(f"AI:     {m['model']}, {m['input_tokens'] + m['output_tokens']} tokens, "
              f"{'~' if m.get('cost_estimated') else ''}${m['cost_usd']:.4f}, "
              f"{m['seconds']} s" + (", own key (BYOK)" if m.get("byok") else ""))
    print(f"run:    {result.run_id}")
    print(f"status: {result.status}" + (f" ({result.message})" if result.message else ""))
    print(f"record: {result.record_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

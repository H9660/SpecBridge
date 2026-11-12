"""Eval rounds by hand: start a round, run its tickets in eval mode, collect every result into one folder.

Usage:
  .venv/bin/python scripts/eval_sheet.py init round-01 --set core     # data/eval/round-01/: sheet.csv, checks.csv
  .venv/bin/python scripts/eval_sheet.py run round-01 [--limit 5]     # runs the tickets not run yet (eval mode)
  .venv/bin/python scripts/eval_sheet.py collect round-01             # fills the automatic columns, pages, report.md
Sets: smoke (10 tickets), core (25), categories (every ticket in docs/TEST_TICKETS.md), full (82).
Then score the human columns in sheet.csv (C1-C3: pass / partial / fail; usefulness 1-5) and run collect again.
Guide: docs/EVAL_GUIDE.md.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge import evals  # noqa: E402
from specbridge.env import load_env  # noqa: E402

SECRET_KEYS = ("GEMINI_API_KEY", "ATLASSIAN_API_TOKEN", "SPECBRIDGE_WEBHOOK_SECRET")
COST_PER_TICKET = 0.10     # rough, for the estimate printed before a run


def cmd_init(args):
    folder, rows = evals.init_round(args.round, args.set)
    waiting = [r["id"] for r in rows if not r["jira_key"]]
    print(f"created {folder} with {len(rows)} tickets (set {args.set})")
    if waiting:
        print(f"not in Jira yet: {', '.join(waiting)} - import them first: "
              ".venv/bin/python scripts/import_adversarial.py --file test_tickets_v1.json")
    print(f"next: .venv/bin/python scripts/eval_sheet.py run {args.round}")
    return 0


def cmd_run(args):
    from specbridge.agent.graph import StartError, new_run_id, run_ticket
    from specbridge.agent.preflight import PreflightError
    folder = evals.EVAL_DIR / args.round
    rows = evals.read_csv(folder / "sheet.csv")
    keys = evals.jira_keys()
    for row in rows:
        row["jira_key"] = row.get("jira_key") or keys.get(row["id"], "")
    todo = [r for r in rows if r["jira_key"] and not r.get("run_id")][: args.limit or None]
    if not todo:
        print("nothing to run: every ticket with a Jira key already has a run id")
        return 0
    print(f"{len(todo)} ticket(s) to run in eval mode, about ${len(todo) * COST_PER_TICKET:.2f} and "
          f"{len(todo) * 2}-{len(todo) * 4} minutes. Ctrl-C stops after saving what is done.")
    for n, row in enumerate(todo, 1):
        run_id = new_run_id()
        t = time.time()
        print(f"[{n}/{len(todo)}] {row['id']} ({row['jira_key']}) {row['path']} ...", flush=True)
        try:
            result = run_ticket(row["jira_key"], "eval", run_id)
            print(f"    {result.status} in {time.time() - t:.0f} s")
        except KeyboardInterrupt:
            row["run_id"] = run_id
            evals.write_csv(folder / "sheet.csv", rows, evals.COLUMNS)
            print(f"\nstopped. {row['id']} can be finished with: scripts/run_ticket.py --resume --run-id {run_id}")
            return 130
        except (StartError, PreflightError) as err:
            print(f"    refused: {err}")
            if isinstance(err, PreflightError):
                print("    stopping: fix the brain / network first, then run again")
                break
            continue
        except Exception as err:  # noqa: BLE001 - the run record is written; keep going with the next ticket
            print(f"    failed: {type(err).__name__}: {str(err)[:200]}")
        row["run_id"] = run_id
        evals.write_csv(folder / "sheet.csv", rows, evals.COLUMNS)
    print(f"next: .venv/bin/python scripts/eval_sheet.py collect {args.round}")
    return 0


def cmd_collect(args):
    env = load_env()
    rows = evals.collect(args.round, secrets=[env.get(k, "") for k in SECRET_KEYS])
    folder = evals.EVAL_DIR / args.round
    ran = sum(1 for r in rows if r.get("run_id"))
    print(f"collected {ran} of {len(rows)} tickets -> {folder / 'sheet.csv'}, {folder / 'report.md'}, pages in "
          f"{folder / 'pages'}")
    print((folder / "report.md").read_text(encoding="utf-8").split("## Per category")[0])
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Eval rounds: init, run, collect.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init")
    p.add_argument("round")
    p.add_argument("--set", default="core", choices=list(evals.SETS))
    p = sub.add_parser("run")
    p.add_argument("round")
    p.add_argument("--limit", type=int, default=0, help="run at most this many tickets now")
    p = sub.add_parser("collect")
    p.add_argument("round")
    args = parser.parse_args(argv)
    try:
        return {"init": cmd_init, "run": cmd_run, "collect": cmd_collect}[args.command](args)
    except (ValueError, FileNotFoundError) as err:
        print(f"refused: {err}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

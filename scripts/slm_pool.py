"""Check the SLM hosts SpecBridge would use (ADR D31): one line per host in SLM_BASE_URLS (or SLM_BASE_URL).

Usage:
  .venv/bin/python scripts/slm_pool.py status            # check every host once
  .venv/bin/python scripts/slm_pool.py status --watch    # again every 5 s, until Ctrl-C
  .venv/bin/python scripts/slm_pool.py status --json     # the same as JSON
Reads .env like a run does (BRAIN=slm is assumed). Exit codes: 0 at least one host is usable, 1 none, 2 bad settings.
"""
import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge import slm_pool  # noqa: E402
from specbridge.brain import BrainError  # noqa: E402
from specbridge.env import load_env  # noqa: E402

COLUMNS = ("host", "state", "queued", "running", "here: answers/errors", "seen", "round trip", "models")


def _cell(value, empty="-"):
    return empty if value is None else str(value)


def rows(report):
    out = []
    for h in report["hosts"]:
        models = "-" if h["models"] is None else ("all pulled" if h["ready"] else ", ".join(h["models"]) or "none")
        state = h["state"] + (f" ({h['reason']})" if h["reason"] else "")
        out.append((h["name"], state, _cell(h["queued"]), _cell(h["running"]),
                    f"{h['answers_here']}/{h['errors_here']}",
                    "-" if h["last_seen_seconds"] is None else f"{h['last_seen_seconds']:.0f}s ago",
                    "-" if h["rtt_ms"] is None else f"{h['rtt_ms']} ms", models))
    return out


def table(report):
    body = [COLUMNS] + rows(report)
    widths = [max(len(r[i]) for r in body) for i in range(len(COLUMNS))]
    lines = ["  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in body]
    lines.insert(1, "  ".join("-" * w for w in widths))
    lines.append(f"\n{report['usable']} of {len(report['hosts'])} host(s) usable  (from {report['hosts_env']})")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="Check the SLM hosts (ADR D31).")
    p.add_argument("command", choices=["status"])
    p.add_argument("--watch", action="store_true", help="check again every 5 s until Ctrl-C")
    p.add_argument("--json", action="store_true", help="print JSON instead of a table")
    a = p.parse_args(argv)
    env = {**load_env(), "BRAIN": "slm"}
    try:
        while True:
            try:
                report = slm_pool.health_report(env)
            except BrainError as err:
                print(f"settings: {err}", file=sys.stderr)
                return 2
            print(json.dumps(report, indent=2) if a.json else table(report), flush=True)
            if not a.watch:
                return 0 if report["usable"] else 1
            time.sleep(5)
            print()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())

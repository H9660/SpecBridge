"""One JSON record per run: data/runs/<ticket>/<run_id>.json (D11). Written however the run ends.

Feeds evaluation (Step 9), debugging and the cost / time measures. data/runs/ is git-ignored.
Holds no keys: only the brain's name, provider and model.
"""
import json
import re
import time
from dataclasses import asdict

from specbridge.env import PROJECT

RUNS = PROJECT / "data" / "runs"
SNAPSHOTS = PROJECT / "data" / "snapshots.json"
TICKET_KEY = re.compile(r"[A-Z][A-Z0-9]+-\d+")
KEPT = ("ticket", "understanding", "clarification", "brief", "work_items", "e2e", "skipped",
        "orchestration", "results", "plan", "review", "page", "saved", "published")   # grows as nodes are added
PAGE_FILES_ONLY = ("html", "markdown")   # copies of the page that save_local writes as files, not kept here


def frozen_commits():
    try:
        repos = json.loads(SNAPSHOTS.read_text(encoding="utf-8"))["repos"]
        return {name: r["commit"] for name, r in repos.items()}
    except (OSError, KeyError, ValueError):
        return {}


def _kept(key, value):
    if key == "page" and isinstance(value, dict):
        return {k: v for k, v in value.items() if k not in PAGE_FILES_ONLY}
    return value


def path_for(state, records_dir=RUNS):
    """The ticket key from intake, else one found in what the user gave, else "unknown"."""
    key = (state.get("ticket") or {}).get("key") or ""
    if not TICKET_KEY.fullmatch(key):
        found = TICKET_KEY.search((state.get("ticket_ref") or "").upper())
        key = found.group(0) if found else "unknown"
    return records_dir / key / f"{state['run_id']}.json"


def write(state, settings, status, records_dir=RUNS, error=None, brain=None, note=""):
    path = path_for(state, records_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    record = {
        "run_id": state["run_id"], "ticket_ref": state.get("ticket_ref"), "mode": state.get("mode"),
        "status": status, "error": error, "note": note,
        "started_at": state.get("started_at"), "finished_at": now,
        "wall_seconds": round(now - state.get("started_at", now), 3),
        "rounds": state.get("round", 0), "spent": state.get("spent", {}), "trace": state.get("trace", []),
        "brain": brain, "settings": asdict(settings), "frozen_commits": frozen_commits(),
        "state": {k: _kept(k, state.get(k)) for k in KEPT},
    }
    path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
    return path

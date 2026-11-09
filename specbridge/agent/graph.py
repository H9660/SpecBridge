"""The main LangGraph graph (ARCHITECTURE.md, docs/architecture.drawio), built node by node.

Now: START -> intake -> understand -> END. `run_ticket` is START: it checks the request and the brain, creates the
run, runs the graph with a checkpointer, and writes the run record however the run ends.

Nodes are plain functions `node(state, settings)`; `build_graph` takes replacements, which is how
tests use fakes and each real node replaces its placeholder.
"""
import os
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from specbridge.agent import preflight, run_record
from specbridge.agent.limits import load_settings
from specbridge.agent.nodes import intake, understand
from specbridge.agent.state import ENABLED_MODES, MODES, SpecBridgeState, add_spent

DEFAULT_NODES = {"intake": intake.node, "understand": understand.node}
ORDER = ("intake", "understand")   # grows as nodes are built
MAX_REF_CHARS = 2000
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


class StartError(ValueError):
    """The request was refused before a run was created."""


@dataclass
class RunResult:
    run_id: str
    status: str             # complete | paused | (already finished: its earlier status)
    state: dict
    record_path: object
    brain: dict | None = None
    message: str = ""


def _main_node(name, fn, settings):
    def wrapped(state):
        t0 = time.time()
        out = dict(fn(state, settings) or {})
        dt = time.time() - t0
        out["spent"] = add_spent(out.get("spent"), {"seconds": dt})
        out["trace"] = [{"node": name, "round": out.get("round", state.get("round", 0)), "seconds": round(dt, 4)}]
        return out
    return wrapped


def build_graph(nodes=None, settings=None, checkpointer=None, interrupt_before=None):
    settings = settings or load_settings()
    fns = {**DEFAULT_NODES, **(nodes or {})}
    g = StateGraph(SpecBridgeState)
    for name in ORDER:
        g.add_node(name, _main_node(name, fns[name], settings))
    for a, b in zip((START, *ORDER), (*ORDER, END)):
        g.add_edge(a, b)
    return g.compile(checkpointer=checkpointer, interrupt_before=interrupt_before)


def sqlite_checkpointer(records_dir=run_record.RUNS):
    return SqliteSaver(sqlite3.connect(records_dir / "checkpoints.sqlite", check_same_thread=False))


def new_run_id():
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def _check_request(ticket_ref, mode, run_id, resume):
    if mode not in MODES:
        raise StartError(f"unknown mode {mode!r}; choose one of {', '.join(ENABLED_MODES)}")
    if mode not in ENABLED_MODES:
        raise StartError("live mode needs the publish node, which is not built yet; use --mode dry-run")
    if run_id is not None and not RUN_ID.fullmatch(run_id):
        raise StartError("a run id may only use letters, digits, '.', '_' and '-' (at most 64)")
    if resume:
        if not run_id:
            raise StartError("--resume needs --run-id of the run to continue")
        return None
    ref = (ticket_ref or "").strip()
    if not ref:
        raise StartError("give a ticket URL or key, e.g. SPEC-12")
    if len(ref) > MAX_REF_CHARS:
        raise StartError(f"the ticket reference is {len(ref)} characters; at most {MAX_REF_CHARS} are allowed")
    return ref


def _ready_records_dir(records_dir):
    try:
        records_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise StartError(f"cannot create {records_dir}: {err}") from None
    if not os.access(records_dir, os.W_OK):
        raise StartError(f"cannot write to {records_dir}")


def run_ticket(ticket_ref=None, mode="dry-run", run_id=None, resume=False, preflight_check=True, *,
               settings=None, nodes=None, checkpointer=None, records_dir=run_record.RUNS, env=None,
               brain_check=preflight.check_brain, interrupt_before=None):
    """START a run (or continue one with resume=True and its run_id) and return a RunResult.

    Refusals before a run exists raise StartError, SettingsError or PreflightError and write nothing.
    Once the run exists, a record is written however it ends; a crash or Ctrl-C is re-raised after that.
    """
    ref = _check_request(ticket_ref, mode, run_id, resume)
    settings = settings or load_settings(env)
    _ready_records_dir(records_dir)
    checkpointer = checkpointer or sqlite_checkpointer(records_dir)
    run_id = run_id or new_run_id()
    config = {"configurable": {"thread_id": run_id}, "recursion_limit": settings.recursion_limit,
              "max_concurrency": settings.max_concurrency}
    exists = checkpointer.get_tuple(config) is not None
    if resume and not exists:
        raise StartError(f"no such run: {run_id}")
    if not resume and exists:
        raise StartError(f"run id {run_id} is already used; leave --run-id out for a new run")
    brain = brain_check(env=env, network=preflight_check)
    app = build_graph(nodes, settings, checkpointer, interrupt_before)

    if resume:
        snapshot = app.get_state(config)
        if not snapshot.next:
            values = snapshot.values
            return RunResult(run_id, values.get("status", "complete"), values,
                             run_record.path_for(values, records_dir), brain, "this run already finished")
        start = None
    else:
        start = {"run_id": run_id, "mode": mode, "ticket_ref": ref, "started_at": time.time(), "round": 0,
                 "trace": [{"node": "START", "round": 0, "seconds": 0.0}], "spent": {}}

    def record(status, error=None):
        values = app.get_state(config).values
        return run_record.write(values, settings, status, records_dir, error, brain)

    try:
        state = app.invoke(start, config)
    except KeyboardInterrupt:
        record("interrupted", "stopped by the user (Ctrl-C)")
        raise
    except Exception as err:
        record("error", f"{type(err).__name__}: {err}")
        raise
    status = "paused" if app.get_state(config).next else "complete"
    return RunResult(run_id, status, state, record(status), brain)

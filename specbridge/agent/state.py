"""State of the main graph (ARCHITECTURE.md section 5). Fields are added as their nodes are built.

Plain dicts, so checkpoints and run records are JSON. Fields with a reducer are combined, not
replaced, when several nodes or parallel workers write them: `trace` is appended, `spent` is summed.
"""
import operator
from typing import Annotated, Literal, TypedDict

MODES = ("dry-run", "eval", "live")
ENABLED_MODES = ("dry-run", "eval", "live")   # live publishes to Confluence and Jira (node 11)


def add_spent(a, b):
    """Sum tokens, cost and seconds from nodes and parallel workers."""
    out = dict(a or {})
    for k, v in (b or {}).items():
        out[k] = out.get(k, 0) + v
    return out


class SpecBridgeState(TypedDict, total=False):
    # set by START
    run_id: str
    mode: Literal["dry-run", "eval", "live"]
    ticket_ref: str          # what the user gave: a ticket URL or key, trimmed
    started_at: float
    round: int
    # written by nodes
    ticket: dict             # intake
    understanding: dict      # understand
    clarification: dict      # clarify (only for tickets without test cases)
    brief: dict              # orchestrator: shared, read-only context for every worker
    work_items: list         # orchestrator: {id, criterion_ids, slice, seed_evidence, budget} per worker
    e2e: dict | None         # orchestrator: the end-to-end worker's input, if it runs
    skipped: list            # orchestrator: criteria no worker gets, with the reason
    orchestration: dict      # orchestrator: how the plan was made (search mode, AI or code, budget)
    results: Annotated[list, operator.add]   # one WorkerResult per worker (parallel workers append)
    plan: dict               # merge: the ticket's test plan (criteria coverage, TC cases, EV evidence, ...)
    review: dict             # reviewer: verdict per criterion, flags, scores, retry list, final status
    page: dict               # render: title, labels, storage (Confluence), html, markdown, comment, summary
    saved: dict              # save_local: folder, files (html, markdown, storage, comment), bytes, warnings, error
    published: dict          # publish: page id / url / action / version, Jira comment id / action, error, fallback
    status: str              # set by a node that decides the outcome, e.g. clarify: "needs-clarification"
    trace: Annotated[list, operator.add]     # {node, round, seconds} per node, in run order
    spent: Annotated[dict, add_spent]        # {tokens, cost, seconds}

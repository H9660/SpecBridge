"""e2e_worker (node 6): end-to-end flows that pass through several acceptance criteria.

Runs only when the orchestrator planned 2+ criterion workers in full scope (state["e2e"]), in parallel with them
and independent of them (D17). It is the criterion worker's subgraph in "e2e" mode (criterion_worker.py): a
one-line summary of every criterion instead of a slice, no starting files, 4 tool calls to confirm the screens
and the navigation between them, prompts/e2e.md for writing, and at most 3 flows, each through 2+ criteria
and citing code it read.
"""
from specbridge.agent.worker import criterion_worker

WORK_ITEM_ID = "E2E"


def as_work_item(e2e):
    """The orchestrator's e2e input as a work item for the shared subgraph."""
    criteria = [{"id": c["id"], "text": c["text"], "source": "summary", "quote": ""} for c in e2e["criteria"]]
    return {"id": WORK_ITEM_ID, "mode": "e2e", "criterion_ids": [c["id"] for c in criteria],
            "slice": {"focus": "flows that pass through several criteria", "criteria": criteria, "ticket_lines": []},
            "screens": list(e2e.get("screens", [])), "seed_evidence": [], "budget": dict(e2e["budget"])}


make_run = criterion_worker.make_run
run = make_run()

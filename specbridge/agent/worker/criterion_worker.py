"""criterion_worker: one subagent per work item, with its own private state (ARCHITECTURE.md D15-D18, ADR D23).

receive_slice -> agent <-> tools -> write_cases -> finish
- receive_slice (code): the shared brief, its own criteria and ticket lines, its starting files, its limits.
- agent (AI, cheap model - brains.json role "worker_agent"): each turn one JSON action {thought, action, args_json}:
  search_code, read_file, grep, find_usages or done (D6). At most `tool_calls` actions; stops early on its budget.
- tools (code): runs the action through the code source, records what was read as evidence E1, E2, ... (D7) and
  compacts old tool output when the conversation nears the context cap (D8).
- write_cases (AI, main model): one call writes the test cases from the evidence.
- finish (code): keeps only cases for its own criteria that cite evidence it really read; redacts secrets and drops
  cases that read like instructions to an AI (D3); sets status complete | needs_more | budget_hit.
Only the WorkerResult leaves the worker; its conversation stays in its own checkpointed state (D16).

The same subgraph runs the e2e worker (node 6) when the work item has mode "e2e" (see e2e_worker.py): it gets a
summary of every criterion, confirms screens and navigation with its few tool calls, writes 1-3 flows with
prompts/e2e.md, and each flow must span at least 2 criteria.
"""
import json
import threading
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from specbridge import ticket_text
from specbridge.agent.code_source import LibrarySource, ToolCache
from specbridge.agent.nodes.understand import load_prompt
from specbridge.agent.worker import evidence as ev
from specbridge.agent.worker import tools as tl
from specbridge.brain import BrainError, load_brain
from specbridge.env import PROJECT, load_env

AGENT_PROMPT = PROJECT / "prompts" / "worker_agent.md"
CASES_PROMPT = PROJECT / "prompts" / "write_cases.md"
E2E_PROMPT = PROJECT / "prompts" / "e2e.md"
MAX_FLOWS = 3
AGENT_MAX_TOKENS = 2000
CASES_MAX_TOKENS = 8000
CONTEXT_CAP = 15_000              # tokens of conversation per worker on the cloud model (D8)
EVIDENCE_CHARS = 48_000           # about 12k tokens of read code given to write_cases
EVIDENCE_ITEM_CHARS = 6_000
CASE_TYPES = ["happy", "negative", "edge", "permission", "empty-state"]
STR = {"type": "string"}
LIST = {"type": "array", "items": STR}
ACTION_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["thought", "action", "args_json"],
                 "properties": {"thought": STR, "action": {"type": "string", "enum": tl.NAMES + ["done"]},
                                "args_json": STR}}
CASES_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["cases", "untestable", "questions", "notes", "missing"],
    "properties": {
        "cases": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["criterion_id", "title", "type", "preconditions", "steps", "expected", "evidence_ids"],
            "properties": {"criterion_id": STR, "title": STR, "type": {"type": "string", "enum": CASE_TYPES},
                           "preconditions": LIST, "steps": LIST, "expected": STR, "evidence_ids": LIST}}},
        "untestable": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["criterion_id", "reason"],
            "properties": {"criterion_id": STR, "reason": STR}}},
        "questions": LIST, "notes": LIST, "missing": STR,
    },
}
E2E_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["flows", "questions", "notes", "no_flow_reason"],
    "properties": {
        "flows": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["criterion_ids", "title", "preconditions", "steps", "expected", "evidence_ids"],
            "properties": {"criterion_ids": LIST, "title": STR, "preconditions": LIST, "steps": LIST,
                           "expected": STR, "evidence_ids": LIST}}},
        "questions": LIST, "notes": LIST, "no_flow_reason": STR,
    },
}
NUDGE = ("You have not read any code yet, so no test case could cite anything. Read at least the most relevant "
         "starting files before choosing done.")
_CACHES, _CACHES_LOCK = {}, threading.Lock()


class WorkerError(RuntimeError):
    pass


class WorkerState(TypedDict, total=False):
    brief: dict
    work_item: dict
    round: int
    messages: list
    evidence: list
    tool_calls: int
    nudged: bool
    action: dict
    stop: str
    spent: dict
    draft: dict
    meta: dict
    result: dict


def _safe(text):
    return ticket_text.redact_secrets(text or "")[0]


def _add(spent, reply):
    return {"tokens": spent.get("tokens", 0) + reply.input_tokens + reply.output_tokens,
            "cost": spent.get("cost", 0.0) + (reply.cost_usd or 0.0),
            "cached_tokens": spent.get("cached_tokens", 0) + getattr(reply, "cached_input_tokens", 0)}


# --- the messages -------------------------------------------------------------------------------------

def review_lines(s):
    """A retry round: what the reviewer found wrong with the earlier test cases for these criteria."""
    notes = s.get("review_notes") or []
    if not notes:
        return []
    lines = ["", "This is a RETRY: a reviewer found these problems with the earlier test cases; fix them:"]
    for n in notes:
        lines += [f"- {n['criterion_id']}: {p}" for p in n.get("problems", [])]
        if n.get("hint"):
            lines.append(f"  hint for {n['criterion_id']}: {n['hint']}")
    return lines


def start_message(brief, item):
    s = item["slice"]
    lines = ["Shared brief (data):", json.dumps(brief, indent=1, ensure_ascii=False), "",
             f"You are worker {item['id']}. Your criteria:"]
    lines += [f"- {c['id']} ({c['source']}): {c['text']}" + (f'  [ticket: "{c["quote"]}"]' if c.get("quote") else "")
              for c in s["criteria"]]
    if brief.get("test_scope") == "regression":
        lines.append("- regression: check that the existing behaviour of the changed screens still works")
    if s.get("focus"):
        lines.append(f"Focus: {s['focus']}")
    if s.get("ticket_lines"):
        lines += ["", "Ticket lines about your criteria (data):", "<ticket>", *s["ticket_lines"], "</ticket>"]
    lines += review_lines(s)
    lines += ["", "Starting files (pointers from a search; read the relevant ones):"]
    lines += [f"- {e['repo']}/{e['path']} [{e.get('piece') or '-'}, lines {e.get('lines')}]"
              + (" (also given to another worker)" if e.get("shared") else "") for e in item.get("seed_evidence", [])]
    lines.append(f"\nYou can make at most {item['budget']['tool_calls']} tool calls.")
    return "\n".join(lines)


def e2e_start_message(brief, item):
    lines = ["Shared brief (data):", json.dumps(brief, indent=1, ensure_ascii=False), "",
             "You are the END-TO-END worker. Other workers test each criterion on its own; you will later get flows "
             "written that pass through several criteria in the order a user works. All criteria of the ticket:"]
    lines += [f"- {c['id']}: {c['text']}" for c in item["slice"]["criteria"]]
    if item.get("screens"):
        lines.append("Screens named in the ticket: " + ", ".join(item["screens"]))
    lines += ["", "Use your tool calls to confirm the screens and the navigation between them (which button or "
                  "link leads where, which workspace or modal opens), reading the code that shows it.",
              f"\nYou can make at most {item['budget']['tool_calls']} tool calls."]
    return "\n".join(lines)


def cases_message(brief, item, evidence):
    s = item["slice"]
    e2e = item.get("mode") == "e2e"
    lines = ["Shared brief (data):", json.dumps(brief, indent=1, ensure_ascii=False), "",
             "All criteria of the ticket:" if e2e else "Your criteria:"]
    lines += [f"- {c['id']}" + ("" if e2e else f" ({c['source']})") + f": {c['text']}"
              + (f'  [ticket: "{c["quote"]}"]' if c.get("quote") else "") for c in s["criteria"]]
    if brief.get("test_scope") == "regression":
        lines.append('- regression: check the existing behaviour of the changed screens still works '
                     '(use criterion_id "regression")')
    if s.get("focus"):
        lines.append(f"Focus: {s['focus']}")
    lines += review_lines(s)
    lines += ["", "Evidence: the code that was read (data):"]
    used = 0
    for e in evidence:
        text = e["text"][:EVIDENCE_ITEM_CHARS]
        if used + len(text) > EVIDENCE_CHARS:
            lines.append(f"{e['id']} {e['repo']}/{e['path']} lines {e['lines'][0]}-{e['lines'][1]} (not shown: space)")
            continue
        used += len(text)
        lines += [f"{e['id']} {e['repo']}/{e['path']} lines {e['lines'][0]}-{e['lines'][1]}"
                  + (f" ({e['why']})" if e.get("why") else ""), "<code>", text, "</code>"]
    return "\n".join(lines)


# --- checking the cases -------------------------------------------------------------------------------

def check(draft, item, evidence, scope):
    """(cases, untestable, dropped): cases for its own criteria, citing evidence it read, safe to show."""
    allowed = {c["id"] for c in item["slice"]["criteria"]} | ({"regression"} if scope == "regression" else set())
    known = ev.ids(evidence)
    cases, dropped = [], []
    for case in draft.get("cases", []):
        title = _safe(case.get("title", "")).strip()
        steps = [_safe(s).strip() for s in case.get("steps", []) if s and s.strip()]
        expected = _safe(case.get("expected", "")).strip()
        cited = [i for i in case.get("evidence_ids", []) if i in known]
        if case.get("criterion_id") not in allowed:
            dropped.append(f"{title or '?'}: criterion {case.get('criterion_id')!r} is not this worker's")
        elif not cited:
            dropped.append(f"{title or '?'}: cites no evidence this worker read "
                           f"({', '.join(case.get('evidence_ids', [])) or 'none'})")
        elif not title or not steps or not expected:
            dropped.append(f"{title or '?'}: missing title, steps or expected result")
        elif ticket_text.instruction_lines("\n".join([title, *steps, expected])):
            dropped.append(f"{title}: reads like an instruction to an AI")
        else:
            cases.append({"id": f"{item['id']}-C{len(cases) + 1}", "criterion_id": case["criterion_id"],
                          "title": title, "type": case.get("type", "happy"),
                          "preconditions": [_safe(p).strip() for p in case.get("preconditions", []) if p.strip()],
                          "steps": steps, "expected": expected, "evidence_ids": cited})
    untestable = [{"criterion_id": u.get("criterion_id"), "reason": _safe(u.get("reason", ""))}
                  for u in draft.get("untestable", []) if u.get("criterion_id") in allowed]
    return cases, untestable, dropped


def check_e2e(draft, item, evidence):
    """(flows, dropped): flows through 2+ of the ticket's criteria, citing evidence it read, safe to show."""
    allowed = {c["id"] for c in item["slice"]["criteria"]}
    known = ev.ids(evidence)
    flows, dropped = [], []
    for flow in draft.get("flows", []):
        title = _safe(flow.get("title", "")).strip()
        steps = [_safe(s).strip() for s in flow.get("steps", []) if s and s.strip()]
        expected = _safe(flow.get("expected", "")).strip()
        ids = list(dict.fromkeys(flow.get("criterion_ids", [])))
        cited = [i for i in flow.get("evidence_ids", []) if i in known]
        if any(i not in allowed for i in ids):
            dropped.append(f"{title or '?'}: unknown criteria {sorted(set(ids) - allowed)}")
        elif len(ids) < 2:
            dropped.append(f"{title or '?'}: spans only {len(ids)} criterion; single-criterion checks belong to "
                           "the criterion workers")
        elif not cited:
            dropped.append(f"{title or '?'}: cites no evidence this worker read "
                           f"({', '.join(flow.get('evidence_ids', [])) or 'none'})")
        elif not title or not steps or not expected:
            dropped.append(f"{title or '?'}: missing title, steps or expected result")
        elif ticket_text.instruction_lines("\n".join([title, *steps, expected])):
            dropped.append(f"{title}: reads like an instruction to an AI")
        elif len(flows) >= MAX_FLOWS:
            dropped.append(f"{title}: more than {MAX_FLOWS} flows")
        else:
            flows.append({"id": f"E2E-C{len(flows) + 1}", "criterion_id": "e2e", "criterion_ids": ids,
                          "title": title, "type": "e2e",
                          "preconditions": [_safe(p).strip() for p in flow.get("preconditions", []) if p.strip()],
                          "steps": steps, "expected": expected, "evidence_ids": cited})
    return flows, dropped


def status_of(cases, untestable, item, scope, stop):
    if item.get("mode") == "e2e":   # no flow is a valid answer, unless a limit stopped it before it found any
        return ("budget_hit" if not cases and stop and stop != "done" else "complete"), []
    if scope == "regression":
        uncovered = [] if cases else ["regression"]
    else:
        done = {c["criterion_id"] for c in cases} | {u["criterion_id"] for u in untestable}
        uncovered = [c["id"] for c in item["slice"]["criteria"] if c["id"] not in done]
    if not uncovered:
        return "complete", []
    return ("budget_hit" if stop and stop != "done" else "needs_more"), uncovered


# --- the subgraph -------------------------------------------------------------------------------------

def build(agent_brain, writer_brain, source):
    def receive_slice(state):
        version, instructions = load_prompt(AGENT_PROMPT)
        item = state["work_item"]
        first = e2e_start_message(state["brief"], item) if item.get("mode") == "e2e" else \
            start_message(state["brief"], item)
        return {"messages": [{"role": "system", "content": instructions}, {"role": "user", "content": first}],
                "evidence": [], "tool_calls": 0, "nudged": False, "spent": {}, "stop": "",
                "meta": {"agent_prompt": version, "agent_model": agent_brain.model,
                         "writer_model": writer_brain.model, "compacted": 0, "turns": 0}}

    def agent(state):
        item = state["work_item"]
        if state["tool_calls"] >= item["budget"]["tool_calls"]:
            return {"stop": "tool-call limit reached"}
        if state["spent"].get("cost", 0) >= item["budget"]["cost"]:
            return {"stop": "cost budget reached"}
        try:
            reply = agent_brain.chat(state["messages"], ACTION_SCHEMA, max_tokens=AGENT_MAX_TOKENS)
        except BrainError as err:
            return {"stop": f"AI error while searching: {str(err)[:200]}"}
        action = reply.data
        messages = state["messages"] + [{"role": "assistant", "content": json.dumps(action, ensure_ascii=False)}]
        out = {"messages": messages, "action": action, "spent": _add(state["spent"], reply),
               "meta": {**state["meta"], "turns": state["meta"]["turns"] + 1}}
        if action["action"] == "done":
            if not state["evidence"] and not state["nudged"]:
                return {**out, "messages": messages + [{"role": "user", "content": NUDGE}], "nudged": True,
                        "action": {}}
            return {**out, "stop": "done"}
        return out

    def route_after_agent(state):
        if state.get("stop"):
            return "write_cases"
        return "tools" if state.get("action") else "agent"

    def tools(state):
        action = state["action"]
        evidence = [dict(e) for e in state["evidence"]]
        args, problem = tl.parse_args(action.get("args_json"))
        text, _ = (f"TOOL ERROR: {problem}", []) if problem else \
            tl.run(source, action["action"], args, evidence, why=_safe(action.get("thought", ""))[:160])
        messages, n = ev.compact(state["messages"] + [{"role": "user", "content": text}], CONTEXT_CAP)
        return {"messages": messages, "evidence": evidence, "tool_calls": state["tool_calls"] + 1, "action": {},
                "meta": {**state["meta"], "compacted": state["meta"]["compacted"] + n}}

    def write_cases(state):
        e2e = state["work_item"].get("mode") == "e2e"
        if not state["evidence"]:
            return {"draft": {"cases": [], "flows": [], "untestable": [], "questions": [], "notes": [],
                              "missing": "no code was read, so no test case could be grounded"}}
        version, instructions = load_prompt(E2E_PROMPT if e2e else CASES_PROMPT)
        user = cases_message(state["brief"], state["work_item"], state["evidence"])
        try:
            reply = writer_brain.ask_json(user, E2E_SCHEMA if e2e else CASES_SCHEMA, system=instructions,
                                          max_tokens=CASES_MAX_TOKENS)
        except BrainError as err:
            raise WorkerError(f"the AI could not write the test cases: {str(err)[:300]}") from None
        return {"draft": reply.data, "spent": _add(state["spent"], reply),
                "meta": {**state["meta"], "cases_prompt": version}}

    def finish(state):
        item, scope = state["work_item"], state["brief"].get("test_scope", "full")
        if item.get("mode") == "e2e":
            (cases, dropped), untestable = check_e2e(state["draft"], item, state["evidence"]), []
        else:
            cases, untestable, dropped = check(state["draft"], item, state["evidence"], scope)
        status, uncovered = status_of(cases, untestable, item, scope, state.get("stop"))
        cited = {i for c in cases for i in c["evidence_ids"]}
        draft = state["draft"]
        questions = [_safe(q) for q in draft.get("questions", []) if q and not ticket_text.instruction_lines(q)]
        return {"result": {
            "work_item_id": item["id"], "criterion_ids": item["criterion_ids"], "round": state.get("round", 1),
            "status": status, "cases": cases, "untestable": untestable, "uncovered": uncovered,
            "evidence": [ev.pointer(e) for e in state["evidence"] if e["id"] in cited],
            "evidence_read": len(state["evidence"]), "questions": questions,
            "notes": [_safe(n) for n in draft.get("notes", [])],
            "missing": _safe(draft.get("missing", "") or draft.get("no_flow_reason", "")),
            "dropped": dropped, "stop": state.get("stop") or "done", "spent": state["spent"],
            "meta": {**state["meta"], "tool_calls": state["tool_calls"]}}}

    g = StateGraph(WorkerState)
    for name, fn in (("receive_slice", receive_slice), ("agent", agent), ("tools", tools),
                     ("write_cases", write_cases), ("finish", finish)):
        g.add_node(name, fn)
    g.add_edge(START, "receive_slice")
    g.add_edge("receive_slice", "agent")
    g.add_conditional_edges("agent", route_after_agent, ["tools", "write_cases", "agent"])
    g.add_edge("tools", "agent")
    g.add_edge("write_cases", "finish")
    g.add_edge("finish", END)
    return g.compile()


def shared_cache(run_id):
    """One tool cache per run, shared by its workers."""
    with _CACHES_LOCK:
        return _CACHES.setdefault(run_id or "-", ToolCache())


def make_run(env=None, agent_brain=None, writer_brain=None, source=None):
    """The worker as a function for the main graph: (payload, settings) -> WorkerResult.
    payload = {brief, work_item, round, run_id}. Tests pass fake brains and a fake source."""
    def run(payload, settings):
        e = load_env() if env is None else env
        agent = agent_brain or load_brain(env=e, role="worker_agent")
        writer = writer_brain or load_brain(env=e)
        src = source or LibrarySource(e, shared_cache(payload.get("run_id")))
        try:
            graph = build(agent, writer, src)
            limit = 4 * payload["work_item"]["budget"]["tool_calls"] + 12
            out = graph.invoke({"brief": payload["brief"], "work_item": payload["work_item"],
                                "round": payload.get("round", 1)}, {"recursion_limit": limit})
            return out["result"]
        finally:
            if source is None:
                src.close()
    return run


run = make_run()

"""merge: all workers' draft cases -> one test plan for the ticket (ADR D24).

A. Code (always): newest result per worker; one evidence list EV-01.. (the same file and lines, or a range inside
   a bigger range of the same file, become one entry); cases ordered by criterion then type (e2e flows last) and
   numbered TC-01..; a coverage status per criterion (covered, untestable, uncovered, skipped, failed, regression);
   preconditions shared by at least half of the cases moved to common_preconditions; questions and notes
   de-duplicated; secrets redacted.
B. One AI editing pass (prompts/merge_editor.md), only with 2+ workers or more than 8 cases. It can only suggest
   `remove` (a duplicate) and `rename` (one name for a screen / button). Code checks every suggestion: a removal
   needs the same criteria, the same type and mostly the same steps, and never takes a criterion's last case; a
   rename must go to a real name from the code, the brief or the ticket. Then the whole plan is checked again
   (every covered criterion still covered, every citation exists, no new ids); if that fails, the AI's edits are
   all dropped. Every applied and refused suggestion is listed in plan["changes"].
Out: state["plan"].
"""
import re

from specbridge import ticket_text
from specbridge.agent.nodes.understand import load_prompt
from specbridge.brain import BrainError, load_brain
from specbridge.env import PROJECT, load_env

PROMPT = PROJECT / "prompts" / "merge_editor.md"
TYPE_ORDER = {"happy": 0, "negative": 1, "edge": 2, "permission": 3, "empty-state": 4, "e2e": 5}
COMMON_SHARE = 0.5        # a precondition in at least half of the cases is written once, at the top
AI_MIN_WORKERS, AI_MAX_CASES_WITHOUT = 2, 8
DUPLICATE_OVERLAP = 0.6   # word overlap of steps + expected for a removal to be accepted
MAX_TOKENS = 3000
STR = {"type": "string"}
SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["remove", "rename"],
    "properties": {
        "remove": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["case", "duplicate_of", "reason"],
            "properties": {"case": STR, "duplicate_of": STR, "reason": STR}}},
        "rename": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["from", "to"],
            "properties": {"from": STR, "to": STR}}},
    },
}


def _safe(text):
    return ticket_text.redact_secrets(text or "")[0]


def _norm(text):
    return " ".join((text or "").casefold().split()).rstrip(".")


def _words(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").casefold()))


# --- A. code ------------------------------------------------------------------------------------------

def latest_results(results):
    """The newest result for each work item (a retry round's result replaces the earlier one)."""
    newest = {}
    for r in results:
        key = r.get("work_item_id")
        if key not in newest or r.get("round", 1) >= newest[key].get("round", 1):
            newest[key] = r
    return list(newest.values())


def merge_evidence(results):
    """(evidence [EV-01..], {(worker, local id): EV id}). Exact duplicates and ranges inside a bigger range of
    the same file become one entry."""
    entries = [(r["work_item_id"], e) for r in results for e in r.get("evidence", [])]
    entries.sort(key=lambda we: (we[1]["repo"], we[1]["path"], we[1]["lines"][0], -we[1]["lines"][1]))
    kept, mapping = [], {}
    for worker, e in entries:
        start, end = e["lines"]
        home = next((k for k in kept if (k["repo"], k["path"]) == (e["repo"], e["path"])
                     and k["lines"][0] <= start and end <= k["lines"][1]), None)
        if home is None:
            home = {"id": f"EV-{len(kept) + 1:02d}", "repo": e["repo"], "path": e["path"], "lines": [start, end],
                    "excerpt": e.get("excerpt", ""), "why": e.get("why", "")}
            kept.append(home)
        mapping[(worker, e["id"])] = home["id"]
    return kept, mapping


def gather_cases(results, mapping, criteria_order):
    cases = []
    for r in results:
        for c in r.get("cases", []):
            ids = c.get("criterion_ids") or [c["criterion_id"]]
            cited = list(dict.fromkeys(mapping[(r["work_item_id"], e)] for e in c.get("evidence_ids", [])
                                       if (r["work_item_id"], e) in mapping))
            cases.append({"criterion_ids": ids, "type": c.get("type", "happy"), "title": _safe(c["title"]),
                          "preconditions": [_safe(p) for p in c.get("preconditions", [])],
                          "steps": [_safe(s) for s in c.get("steps", [])], "expected": _safe(c["expected"]),
                          "evidence_ids": cited, "source": c["id"]})
    big = len(criteria_order) + 1

    def key(c):
        if c["type"] == "e2e":
            return (big, 0, c["source"])
        first = min((criteria_order.index(i) for i in c["criterion_ids"] if i in criteria_order), default=big - 1)
        return (first, TYPE_ORDER.get(c["type"], 9), c["source"])
    return sorted(cases, key=key)


def number(cases):
    return [{"id": f"TC-{n:02d}", **c} for n, c in enumerate(cases, 1)]


def common_preconditions(cases):
    """(common, cases without them): a precondition in at least half of the cases (2+ cases) is written once."""
    if len(cases) < 2:
        return [], cases
    counts, wording = {}, {}
    for c in cases:
        for p in {_norm(x) for x in c["preconditions"]}:
            counts[p] = counts.get(p, 0) + 1
        for x in c["preconditions"]:
            wording.setdefault(_norm(x), x.strip())
    common = [p for p, n in counts.items() if n >= max(2, COMMON_SHARE * len(cases))]
    common.sort(key=lambda p: -counts[p])
    out = [{**c, "preconditions": [x for x in c["preconditions"] if _norm(x) not in common]} for c in cases]
    return [wording[p] for p in common], out


def coverage(understanding, results, skipped, cases):
    scope = understanding.get("test_scope", "full")
    skip = {s["criterion_id"]: s["reason"] for s in skipped}
    untestable = {u["criterion_id"]: u["reason"] for r in results for u in r.get("untestable", [])}
    failed = {cid for r in results if r.get("status") == "error" for cid in r.get("criterion_ids", [])}
    rows = []
    for c in understanding.get("criteria", []):
        cid = c["id"]
        tc = [x["id"] for x in cases if cid in x["criterion_ids"]]
        if scope == "regression":
            status, detail = "regression", "checked through the regression cases"
            tc = [x["id"] for x in cases if "regression" in x["criterion_ids"]]
        elif cid in skip:
            status, detail = "skipped", skip[cid]
        elif tc:
            status, detail = "covered", ""
        elif cid in untestable:
            status, detail = "untestable", untestable[cid]
        elif cid in failed:
            status, detail = "failed", "its worker stopped with an error"
        else:
            status, detail = "uncovered", "no test case and no reason"
        rows.append({"id": cid, "text": _safe(c["text"]), "status": status, "detail": _safe(detail), "cases": tc})
    return rows


def dedupe(items):
    seen, out = set(), []
    for x in items:
        x = _safe((x or "").strip())
        if x and _norm(x) not in seen and not ticket_text.instruction_lines(x):
            seen.add(_norm(x))
            out.append(x)
    return out


def build_plan(state):
    """Part A: the plan made by code alone."""
    u = state.get("understanding") or {}
    results = latest_results(state.get("results") or [])
    evidence, mapping = merge_evidence(results)
    order = [c["id"] for c in u.get("criteria", [])]
    common, cases = common_preconditions(gather_cases(results, mapping, order))
    cases = number(cases)
    return {
        "criteria": coverage(u, results, state.get("skipped") or [], cases),
        "common_preconditions": common, "cases": cases, "evidence": evidence,
        "questions": dedupe(list(u.get("questions", [])) + [q for r in results for q in r.get("questions", [])]),
        "notes": dedupe([n for r in results for n in r.get("notes", [])]),
        "workers": [{"id": r["work_item_id"], "criteria": r.get("criterion_ids", []), "status": r.get("status"),
                     "cases": len(r.get("cases", [])), "stop": r.get("stop", ""), "error": r.get("error", "")}
                    for r in results],
        "changes": [], "editor": {"used": "not needed"},
    }


# --- B. the AI editing pass ---------------------------------------------------------------------------

def real_names(state, plan):
    """Names a rename may use: screens and registered names from the brief, the ticket text, the code excerpts."""
    brief = state.get("brief") or {}
    names = [s.get("name", "") for s in brief.get("screens", [])] + [s.get("registered", "") for s in brief.get("screens", [])]
    corpus = " ".join([*names, (state.get("ticket") or {}).get("text", ""), *(e["excerpt"] for e in plan["evidence"])])
    return [n for n in names if n], corpus.casefold()


def editor_messages(plan, names, instructions):
    lines = ["Real names (screens and registered names from the code): " + (", ".join(names) or "-"), "",
             "Criteria:", *[f"- {c['id']}: {c['text']}" for c in plan["criteria"]], "", "Cases (data):"]
    for c in plan["cases"]:
        lines += [f"{c['id']} [{'+'.join(c['criterion_ids'])}, {c['type']}] {c['title']}",
                  *[f"   pre: {p}" for p in c["preconditions"]], *[f"   step: {s}" for s in c["steps"]],
                  f"   expected: {c['expected']}"]
    return instructions, "\n".join(lines)


def overlap(a, b):
    wa = _words(" ".join(a["steps"] + [a["expected"]]))
    wb = _words(" ".join(b["steps"] + [b["expected"]]))
    return len(wa & wb) / len(wa | wb) if wa | wb else 0.0


def apply_edits(plan, answer, corpus):
    """(cases, changes): accepted removals and renames applied; every suggestion logged with its outcome."""
    cases = [dict(c) for c in plan["cases"]]
    by_id = {c["id"]: c for c in cases}
    changes, removed = [], set()
    for r in answer.get("remove", []):
        a, b = by_id.get(r.get("case")), by_id.get(r.get("duplicate_of"))
        label = f"remove {r.get('case')} (duplicate of {r.get('duplicate_of')})"
        if not a or not b or a is b or a["id"] in removed or b["id"] in removed:
            changes.append({"change": label, "applied": False, "why": "unknown or already removed case"})
        elif set(a["criterion_ids"]) != set(b["criterion_ids"]) or a["type"] != b["type"]:
            changes.append({"change": label, "applied": False, "why": "the cases test different criteria or kinds"})
        elif overlap(a, b) < DUPLICATE_OVERLAP:
            changes.append({"change": label, "applied": False,
                            "why": f"the steps differ too much ({overlap(a, b):.0%} the same)"})
        elif any(not [c for c in cases if c["id"] not in removed | {a["id"]} and cid in c["criterion_ids"]]
                 for cid in a["criterion_ids"]):
            changes.append({"change": label, "applied": False, "why": "it is the last case of a criterion"})
        else:
            removed.add(a["id"])
            changes.append({"change": label, "applied": True, "why": _safe(r.get("reason", ""))[:200],
                            "source": a["source"], "kept": b["source"]})
    cases = [c for c in cases if c["id"] not in removed]
    for r in answer.get("rename", [])[:20]:
        old, new = (r.get("from") or "").strip(), (r.get("to") or "").strip()
        label = f"rename {old!r} -> {new!r}"
        pattern = re.compile(re.escape(old), re.I) if old else None
        texts = lambda c: [c["title"], c["expected"], *c["steps"], *c["preconditions"]]   # noqa: E731
        if not old or not new or _norm(old) == _norm(new):
            changes.append({"change": label, "applied": False, "why": "empty or no change"})
        elif new.casefold() not in corpus:
            changes.append({"change": label, "applied": False, "why": "the new name is not in the code, brief or ticket"})
        elif ticket_text.instruction_lines(new) or _safe(new) != new:
            changes.append({"change": label, "applied": False, "why": "unsafe text"})
        elif not any(pattern.search(t) for c in cases for t in texts(c)):
            changes.append({"change": label, "applied": False, "why": "the old name is not in any case"})
        else:
            for c in cases:
                c["title"], c["expected"] = pattern.sub(new, c["title"]), pattern.sub(new, c["expected"])
                c["steps"] = [pattern.sub(new, s) for s in c["steps"]]
                c["preconditions"] = [pattern.sub(new, p) for p in c["preconditions"]]
            changes.append({"change": label, "applied": True, "why": ""})
    return cases, changes


def plan_ok(before, cases, evidence):
    """The whole-plan checks after the AI's edits."""
    ev_ids = {e["id"] for e in evidence}
    old_ids = {c["id"] for c in before["cases"]}
    covered_before = {i for c in before["cases"] for i in c["criterion_ids"]}
    covered_after = {i for c in cases for i in c["criterion_ids"]}
    return (covered_before <= covered_after and all(set(c["evidence_ids"]) <= ev_ids and c["evidence_ids"]
                                                     for c in cases)
            and {c["id"] for c in cases} <= old_ids
            and all(c["criterion_ids"] == next(o for o in before["cases"] if o["id"] == c["id"])["criterion_ids"]
                    for c in cases))


def edit(plan, state, brain):
    """(plan, spent): part B applied, or part A unchanged with the reason in plan["editor"]."""
    version, instructions = load_prompt(PROMPT)
    names, corpus = real_names(state, plan)
    system, user = editor_messages(plan, names, instructions)
    try:
        reply = brain.ask_json(user, SCHEMA, system=system, max_tokens=MAX_TOKENS)
    except BrainError as err:
        return {**plan, "editor": {"used": "code only", "why": f"AI call failed: {str(err)[:200]}",
                                   "prompt_version": version}}, {}
    spent = {"tokens": reply.input_tokens + reply.output_tokens, "cost": reply.cost_usd or 0.0}
    meta = {"prompt_version": version, "model": reply.model, "cost_usd": reply.cost_usd or 0.0,
            "cost_estimated": reply.cost_estimated, "seconds": reply.seconds}
    cases, changes = apply_edits(plan, reply.data, corpus)
    if not plan_ok(plan, cases, plan["evidence"]):
        return {**plan, "changes": [{**c, "applied": False} for c in changes],
                "editor": {**meta, "used": "code only", "why": "the edited plan failed the whole-plan checks"}}, spent
    renumbered = {c["id"]: f"TC-{n:02d}" for n, c in enumerate(cases, 1)}
    cases = [{**c, "id": renumbered[c["id"]]} for c in cases]
    criteria = [{**row, "cases": [renumbered[i] for i in row["cases"] if i in renumbered]} for row in plan["criteria"]]
    return {**plan, "cases": cases, "criteria": criteria, "changes": changes,
            "editor": {**meta, "used": "AI edits checked by code"}}, spent


# --- the node -----------------------------------------------------------------------------------------

def make_node(brain=None, env=None):
    """merge as a graph node. Tests pass a fake brain."""
    def node(state, settings):
        plan = build_plan(state)
        working = [w for w in plan["workers"] if w["status"] != "error"]
        if len(working) < AI_MIN_WORKERS and len(plan["cases"]) <= AI_MAX_CASES_WITHOUT:
            return {"plan": plan}
        if not plan["cases"]:
            return {"plan": {**plan, "editor": {"used": "not needed (no cases)"}}}
        e = load_env() if env is None else env
        plan, spent = edit(plan, state, brain or load_brain(env=e))
        return {"plan": plan, "spent": spent}
    return node


node = make_node()

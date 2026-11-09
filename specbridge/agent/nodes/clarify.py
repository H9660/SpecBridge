"""clarify (code, no AI): the "needs clarification" result for a ticket that gets no test cases (test_scope "none").

It says why, what was understood, and what the PM should answer, and prepares a short plain-text Jira comment
(fixed templates; the top 5 questions; a placeholder for the link to the full page, filled in by publish). Every
text that may be posted is passed through secret redaction, and questions that read like instructions to an AI
are dropped, so a comment can never repeat an injection (D3). Same input, same output.
Out: state["clarification"], state["status"] = "needs-clarification".
"""
from specbridge import ticket_text

PAGE_LINK = "{page_url}"          # replaced by publish with the UAT page's address
COMMENT_MARKER = "[SpecBridge]"   # lets later runs find and update the same comment (D10)
COMMENT_QUESTIONS = 5
MAX_COMMENT_CHARS = 1500
MAX_COMMENT_LINE = 220

CATEGORIES = {
    "off-domain": {
        "headline": "No UAT test cases: this request does not look like part of OpenMRS.",
        "question": "This does not look like part of a medical record system. Is it intended for OpenMRS, and who "
                    "would use it?",
        "next_step": "Confirm the request is meant for OpenMRS and say who uses it and on which screen."},
    "backend-only": {
        "headline": "No UAT test cases: this change has no visible effect in the browser.",
        "question": "This looks like a server-only change with nothing to check in the browser. Is that right, or "
                    "is there something a user should see?",
        "next_step": "Confirm that no UAT is needed, or describe what a user should see or do differently."},
    "missing-screen": {
        "headline": "No UAT test cases yet: the ticket relies on a screen that is not in the app ({screens}).",
        "question": "\"{screen}\" is not in the app. Is it a new screen to be built, and where should it appear?",
        "next_step": "Say whether the screen is new (and where it goes), or name the existing screen that is meant."},
    "no-criteria": {
        "headline": "No UAT test cases yet: the ticket does not say what should be true when it is done.",
        "question": "What should be true when this is done? Please list what the user should see or be able to do.",
        "next_step": "Add acceptance criteria: what the user should see or be able to do when this is done."},
    "ai-judgement": {
        "headline": "No UAT test cases yet: the ticket could not be turned into checkable steps.",
        "question": "What should a tester be able to see or do in the browser when this is done?",
        "next_step": "Describe the expected behaviour in the browser, step by step if possible."},
}


class ClarifyError(RuntimeError):
    pass


def scope_of(understanding):
    """test_scope, also for answers saved before it existed (understand-v1 / v2)."""
    return understanding.get("test_scope") or ("full" if understanding.get("testable") else "none")


def missing_screens(understanding):
    return [s["name"] for s in understanding.get("screens", [])
            if s.get("role") == "changed" and s.get("status", "existing") == "existing" and s.get("found_in_code") is False]


def category_of(understanding):
    """Why there are no test cases, in the same order as understand's rules."""
    kinds = {r["kind"] for r in understanding.get("risks", [])}
    if understanding.get("domain_fit") == "unrelated":
        return "off-domain"
    if "backend-only" in kinds:
        return "backend-only"
    if missing_screens(understanding):
        return "missing-screen"
    if not [c for c in understanding.get("criteria", []) if c.get("status", "ok") == "ok"]:
        return "no-criteria"
    return "ai-judgement"


def _safe(text):
    return ticket_text.redact_secrets(text or "")[0]


def _cut(text, n):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def questions_for(understanding, category):
    """(questions, dropped): understand's questions, de-duplicated and made safe, or the category's fixed one."""
    out, seen, dropped = [], set(), 0
    for q in understanding.get("questions", []):
        q = _safe((q or "").strip())
        key = " ".join(q.casefold().split())
        if not q or key in seen:
            continue
        if ticket_text.instruction_lines(q):   # never repeat an injected instruction in a comment
            dropped += 1
            continue
        seen.add(key)
        out.append(q)
    if not out:
        template = CATEGORIES[category]["question"]
        screens = missing_screens(understanding)
        out = [template.format(screen=s) for s in screens] if "{screen}" in template and screens else [template]
    return out, dropped


def build_comment(key, headline, reason, questions, next_step):
    """Plain-text Jira comment with the top questions; fewer questions if it would pass MAX_COMMENT_CHARS."""
    shown = min(COMMENT_QUESTIONS, len(questions))
    while True:
        lines = [f"{COMMENT_MARKER} {key}: needs clarification - no UAT test cases yet", "", _cut(headline, 300)]
        if reason:
            lines.append(f"Why: {_cut(reason, 300)}")
        lines += ["", "Questions for the PM:"]
        lines += [f"{i}. {_cut(q, MAX_COMMENT_LINE)}" for i, q in enumerate(questions[:shown], 1)]
        if len(questions) > shown:
            lines.append(f"(+{len(questions) - shown} more on the page)")
        lines += ["", f"To get test cases: {next_step}", f"Full details: {PAGE_LINK}"]
        comment = "\n".join(lines)
        if len(comment) <= MAX_COMMENT_CHARS or shown <= 1:
            return comment
        shown -= 1


def node(state, settings):
    understanding = state.get("understanding")
    if not understanding:
        raise ClarifyError("clarify needs the answer from understand")
    if scope_of(understanding) != "none":
        raise ClarifyError(f"clarify is only for tickets without test cases, but this one has test scope "
                           f"{scope_of(understanding)!r} (the graph routed it wrongly)")
    ticket = state.get("ticket") or {}
    category = category_of(understanding)
    screens = missing_screens(understanding)
    headline = CATEGORIES[category]["headline"].format(screens=", ".join(screens))
    reason = _safe(understanding.get("reason", ""))
    questions, dropped = questions_for(understanding, category)
    next_step = CATEGORIES[category]["next_step"]
    understood = {
        "intent": _safe(understanding.get("intent", "")),
        "criteria": [{k: _safe(c.get(k, "")) for k in ("id", "text", "source", "status")}
                     for c in understanding.get("criteria", [])],
        "screens": [{"name": _safe(s.get("name", "")), "role": s.get("role"), "status": s.get("status", "existing"),
                     "found_in_code": s.get("found_in_code")} for s in understanding.get("screens", [])],
        "roles": understanding.get("roles", []),
    }
    clarification = {
        "category": category, "headline": _safe(headline), "reason": reason, "understood": understood,
        "risks": [{"kind": r["kind"], "detail": _safe(r.get("detail", ""))} for r in understanding.get("risks", [])],
        "questions": questions, "questions_dropped": dropped, "next_step": next_step,
        "comment": _safe(build_comment(ticket.get("key", "?"), headline, reason, questions, next_step)),
        "page_link_placeholder": PAGE_LINK,
    }
    return {"clarification": clarification, "status": "needs-clarification"}

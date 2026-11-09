"""understand (AI, one structured answer): what the ticket asks for, and whether test cases can be written.

1. Prompt from prompts/understand.md (versioned, D12) + a short description of the product + the screens
   registered in the code that are most related to the ticket (ground truth from the frozen repos, picked per
   ticket at run time, ADR D20); the cleaned ticket from intake goes inside a <ticket> data block (D3).
2. One brain.ask_json call with a fixed schema.
3. Code checks the AI cannot talk its way around:
   - a "stated" criterion must quote the ticket exactly, else it becomes "inferred"; ids renumbered AC1..
   - intake's flags always become risks (secret-in-ticket, injection-attempt, partial-ticket)
   - every screen is looked up in the code library; only a screen the ticket treats as EXISTING, changes, and
     that is not in the code makes it untestable (a screen the ticket asks to build is expected to be missing)
   - domain fit: "unrelated" makes it untestable, "doubtful" only adds a risk and a question
   - the final testable decision is made here, by rules (see `decide`)
   - the answer is passed through secret redaction once more
Out: state["understanding"] = {intent, criteria, screens, roles, questions, risks, domain_fit, domain_reason,
testable, reason, test_scope, regression_screens, meta}. test_scope: "full" (test the criteria), "regression"
(a backend-only change to an existing screen's code: check that its existing behaviour still works, ADR D21) or
"none" (not testable; the graph goes to clarify).
"""
import json
import re

from specbridge import ticket_text
from specbridge.brain import BrainError, load_brain
from specbridge.code_index import CodeIndex
from specbridge.env import PROJECT, load_env

PROMPT = PROJECT / "prompts" / "understand.md"
REPOS = PROJECT / "config" / "repos.json"
MAX_TOKENS = 4000          # Gemini thinks before answering; the thinking counts against this
TOO_MANY_CRITERIA = 15
MAX_QUESTIONS = 10
OUT_OF_CREDIT = ("the AI provider refused the call: no credit or quota left. On Google's free tier the limits are "
                 "per minute and per day: wait and resume, or turn on billing for the key at "
                 "https://aistudio.google.com/apikey")
RISK_KINDS = ["contradictory", "backend-only", "unknown-screen", "injection-attempt", "secret-in-ticket",
              "vague", "too-broad", "off-domain", "partial-ticket"]
FLAG_RISKS = {"secret-redacted": ("secret-in-ticket", "the ticket contained secrets; they were removed before the AI saw it"),
              "possible-injection": ("injection-attempt", "the ticket contains text aimed at an AI; it was not followed"),
              "truncated": ("partial-ticket", "the ticket was cut because it is very long; later parts were not read")}

STR = {"type": "string"}
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["intent", "criteria", "screens", "roles", "questions", "risks", "domain_fit", "domain_reason",
                 "testable", "reason"],
    "properties": {
        "intent": STR,
        "criteria": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["text", "source", "quote", "status"],
            "properties": {"text": STR, "source": {"type": "string", "enum": ["stated", "inferred"]}, "quote": STR,
                           "status": {"type": "string", "enum": ["ok", "conflicting", "unclear"]}}}},
        "screens": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "role", "status", "matches"],
            "properties": {"name": STR, "role": {"type": "string", "enum": ["changed", "used"]},
                           "status": {"type": "string", "enum": ["existing", "new"]}, "matches": STR}}},
        "roles": {"type": "array", "items": STR},
        "questions": {"type": "array", "items": STR},
        "risks": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["kind", "detail"],
            "properties": {"kind": {"type": "string", "enum": RISK_KINDS}, "detail": STR}}},
        "domain_fit": {"type": "string", "enum": ["fits", "doubtful", "unrelated"]},
        "domain_reason": STR,
        "testable": {"type": "boolean"},
        "reason": STR,
    },
}


class UnderstandError(RuntimeError):
    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.retryable = retryable


# --- the prompt -------------------------------------------------------------------------------------

def load_prompt(path=PROMPT):
    """(version, instructions). The first line of the file is `version: ...`."""
    first, _, rest = path.read_text(encoding="utf-8").partition("\n")
    if not first.startswith("version:"):
        raise UnderstandError(f"{path.name} must start with a 'version:' line")
    return first.split(":", 1)[1].strip(), rest.strip()


def product_context(path=REPOS):
    apps = json.loads(path.read_text(encoding="utf-8"))["repos"]
    lines = [f"- {a['name']}: {a['role']}" for a in apps]
    return ("The product is OpenMRS 3, an open-source electronic medical record system used by clinics and "
            "hospitals. Its web app is made of these parts:\n" + "\n".join(lines))


def registered_name(line):
    """'widget allergies-list in allergy-list-pills-slot titled X' -> 'allergies-list'."""
    parts = line.split()
    return parts[1] if len(parts) > 1 else ""


def build_messages(ticket, instructions, product, known=()):
    system = f"{instructions}\n\nProduct:\n{product}"
    flags = "\n".join(f"- {f['kind']}: {f['detail']}" for f in ticket.get("flags", [])) or "- none"
    screens = "\n".join(f"- [{repo}] {line}" for repo, line in known) or "- none found"
    user = (f"Notes from the code that fetched the ticket (not part of the ticket):\n{flags}\n\n"
            "Screens registered in the code that look related to this ticket (from the real code - ground truth "
            f"about what exists, but only the closest matches, not every screen):\n{screens}\n\n"
            f"<ticket>\nKey: {ticket['key']}\nType: {ticket.get('type', '')}\n"
            f"Labels: {', '.join(ticket.get('labels', [])) or '-'}\n\n{ticket['text']}\n</ticket>")
    return system, user


# --- checks on the answer ---------------------------------------------------------------------------

def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", text or "")).strip().casefold()


def check_criteria(raw, ticket_body):
    body = _norm(ticket_body)
    out, seen = [], set()
    for c in raw:
        text = (c.get("text") or "").strip()
        if not text or _norm(text) in seen:
            continue
        seen.add(_norm(text))
        quote = (c.get("quote") or "").strip()
        source = c.get("source", "inferred")
        quoted = bool(quote) and _norm(quote) in body
        if source == "stated" and not quoted:
            source = "inferred"
        out.append({"id": f"AC{len(out) + 1}", "text": text, "source": source, "quote": quote if quoted else "",
                    "status": c.get("status", "ok")})
    return out


def check_screens(raw, lookup, known_names=frozenset()):
    """[{name, role, status, matches, found_in_code: True | False | None, where}].

    found_in_code is True when the AI matched it to a registered screen from the list it was given, or the code
    library finds its name; False when the library was searched and has neither; None without a library."""
    out, seen = [], set()
    for s in raw:
        name = (s.get("name") or "").strip()
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        matches = (s.get("matches") or "").strip()
        matched = matches in known_names
        hits = lookup(name) if lookup else None
        found = True if matched or hits else (None if hits is None else False)
        where = [f"registered: {matches}"] if matched else [f"{r}/{p}" for r, p in (hits or [])][:2]
        out.append({"name": name, "role": s.get("role", "used"), "status": s.get("status", "existing"),
                    "matches": matches if matched else "", "found_in_code": found, "where": where})
    return out


def _add_risk(risks, kind, detail):
    for r in risks:
        if r["kind"] == kind:
            return
    risks.append({"kind": kind, "detail": detail})


def _add_question(questions, q):
    if q and _norm(q) not in {_norm(x) for x in questions}:
        questions.append(q)


def regression_screens(screens):
    """Existing screens, found in the code, whose own code the ticket changes."""
    return [s["name"] for s in screens if s["role"] == "changed" and s["status"] == "existing" and s["found_in_code"]]


def decide(answer, criteria, screens, risks, flags):
    """(testable, reason, test_scope) by rules. The AI's own yes/no is used only where no rule applies."""
    kinds = {r["kind"] for r in risks}
    usable = [c for c in criteria if c["status"] == "ok"]
    unknown_changed = [s["name"] for s in screens
                       if s["role"] == "changed" and s["status"] == "existing" and s["found_in_code"] is False]
    if answer.get("domain_fit") == "unrelated":
        return False, f"the request does not fit this product: {answer.get('domain_reason', '').strip()}".rstrip(": "), "none"
    if "backend-only" in kinds:
        touched = regression_screens(screens)
        if touched:   # ADR D21: a refactor of a real screen's code can break it, so check it still works
            return True, ("no visible change, but the code of an existing screen changes: regression check that it "
                          f"still works ({', '.join(touched)})"), "regression"
        return False, ("backend-only change: nothing a user can check in the browser, so UAT test cases do not "
                       "apply"), "none"
    if unknown_changed:
        return False, ("the ticket talks about a screen that does not exist in the code: "
                       f"{', '.join(unknown_changed)}"), "none"
    if not usable:
        return False, "no checkable acceptance criteria could be found or inferred", "none"
    if not answer.get("testable") and "possible-injection" in {f["kind"] for f in flags} and "vague" not in kinds:
        return True, ("test cases can be written; the ticket's text asking the AI to skip them was ignored. "
                      f"(AI said: {answer.get('reason', '').strip()})"), "full"
    if not answer.get("testable"):
        return False, answer.get("reason", "").strip() or "the AI judged the ticket not testable", "none"
    return True, answer.get("reason", "").strip() or "checkable criteria found", "full"


def finish(answer, ticket, lookup=None, known=()):
    """The AI's answer -> the checked Understanding (everything except meta). `known` = the registered screens
    the AI was shown, [(repo, line)]."""
    criteria = check_criteria(answer.get("criteria", []), ticket["text"])
    screens = check_screens(answer.get("screens", []), lookup, {registered_name(line) for _, line in known})
    questions = [q.strip() for q in answer.get("questions", []) if q and q.strip()]
    risks = []
    checked = any(s["found_in_code"] is not None for s in screens)
    for r in answer.get("risks", []):
        if r.get("kind") in RISK_KINDS and not (checked and r["kind"] == "unknown-screen"):   # the code decides that one
            _add_risk(risks, r["kind"], (r.get("detail") or "").strip())
    flags = ticket.get("flags", [])
    for f in flags:
        if f["kind"] in FLAG_RISKS:
            _add_risk(risks, *FLAG_RISKS[f["kind"]])
    if any(c["status"] == "conflicting" for c in criteria):
        _add_risk(risks, "contradictory", "some criteria cannot all be true; they are left out of test cases until the PM decides")
    if len(criteria) > TOO_MANY_CRITERIA:
        _add_risk(risks, "too-broad", f"{len(criteria)} criteria in one ticket")
        _add_question(questions, f"This ticket has {len(criteria)} criteria. Should it be split into smaller tickets?")
    for s in screens:
        if s["status"] == "existing" and s["found_in_code"] is False:
            _add_risk(risks, "unknown-screen", f"not found in the code: {s['name']}")
            _add_question(questions, f"\"{s['name']}\" does not exist in the code: is it a new screen to be built, "
                                     "and where should it appear?" if s["role"] == "changed" else
                          f"\"{s['name']}\" was not found in the code: which existing screen is meant?")
        elif s["status"] == "new" and s["matches"]:
            _add_question(questions, f"\"{s['name']}\" is described as new, but the code already has \"{s['matches']}\". "
                                     "Is this a change to the existing one?")
    if answer.get("domain_fit") in ("doubtful", "unrelated"):
        _add_risk(risks, "off-domain", (answer.get("domain_reason") or "").strip() or "does not look like part of this product")
        _add_question(questions, "This request does not look like part of a medical record system. Is it intended "
                                 "for OpenMRS, and if so, who would use it?")
    testable, reason, scope = decide(answer, criteria, screens, risks, flags)
    result = {"intent": (answer.get("intent") or "").strip(), "criteria": criteria, "screens": screens,
              "roles": sorted({r.strip() for r in answer.get("roles", []) if r and r.strip()}),
              "questions": questions[:MAX_QUESTIONS], "risks": risks,
              "domain_fit": answer.get("domain_fit", "fits"), "domain_reason": (answer.get("domain_reason") or "").strip(),
              "testable": testable, "reason": reason, "test_scope": scope,
              "regression_screens": regression_screens(screens) if scope == "regression" else []}
    return redact_all(result)


def redact_all(value):
    """Secret redaction over every string of the answer (a safety net: intake already removed the secrets)."""
    if isinstance(value, str):
        return ticket_text.redact_secrets(value)[0]
    if isinstance(value, list):
        return [redact_all(v) for v in value]
    if isinstance(value, dict):
        return {k: redact_all(v) for k, v in value.items()}
    return value


# --- the node ---------------------------------------------------------------------------------------

def code_lookup(env):
    """find_screen on the code library in SPECBRIDGE_WORKDIR, or None if there is no library."""
    workdir = env.get("SPECBRIDGE_WORKDIR")
    if not workdir:
        return None
    from pathlib import Path
    db = Path(workdir) / "specbridge_index.sqlite"
    if not db.exists():
        return None
    index = CodeIndex(Path(workdir), db)
    try:
        index.db.execute("SELECT 1 FROM pieces_fts LIMIT 1")
    except Exception:  # noqa: BLE001 - an old or empty library: skip the screen check
        index.close()
        return None
    return index


def make_node(brain=None, env=None, lookup="library", catalogue=None):
    """understand as a graph node. By default both checks use the real code library. Tests pass a fake brain,
    a fake lookup (name -> [(repo, path)]) and a fake catalogue (ticket text -> [(repo, registered screen line)])."""
    def node(state, settings):
        ticket = state.get("ticket")
        if not ticket or not ticket.get("text"):
            raise UnderstandError("understand needs the ticket from intake")
        e = load_env() if env is None else env
        version, instructions = load_prompt()
        index = code_lookup(e) if lookup == "library" else None
        try:
            find = index.find_screen if index else (lookup if callable(lookup) else None)
            listing = index.screens_for if index else catalogue
            known = listing(ticket["text"]) if listing else []
            system, user = build_messages(ticket, instructions, product_context(), known)
            reply = _ask(brain or load_brain(env=e), system, user)
            understanding = finish(reply.data, ticket, find, known)
        finally:
            if index:
                index.close()
        cost = reply.cost_usd or 0.0
        understanding["meta"] = {"model": reply.model, "brain": reply.brain, "prompt_version": version,
                                 "input_tokens": reply.input_tokens, "output_tokens": reply.output_tokens,
                                 "cost_usd": cost, "cost_estimated": reply.cost_estimated,
                                 "cached_input_tokens": reply.cached_input_tokens,
                                 "seconds": reply.seconds, "attempts": reply.attempts, "byok": reply.byok,
                                 "screen_check": "skipped (no code library)" if find is None else "done",
                                 "screens_shown": len(known)}
        return {"understanding": understanding,
                "spent": {"tokens": reply.input_tokens + reply.output_tokens, "cost": cost}}
    return node


def _ask(b, system, user):
    try:
        return b.ask_json(user, SCHEMA, system=system, max_tokens=MAX_TOKENS)
    except BrainError as err:
        text = str(err).lower()
        if "returned 402" in text:   # prepaid credit used up; Google's own reason is safe to show
            reason = str(err).split("tries: ", 1)[-1][:300]
            raise UnderstandError(f"the AI provider refused the call: no credit or quota left (HTTP 402: {reason})",
                                  retryable=True) from None
        if "returned 429" in text and "per day" in text:
            reset = re.search(r"retry in ([0-9hms.]+?)(?:\.\d+)?s\b", text)
            when = f" (resets in {reset.group(1)}s)" if reset else ""
            raise UnderstandError(OUT_OF_CREDIT + when, retryable=True) from None
        raise UnderstandError(f"the AI could not answer: {err}", retryable=True) from None


node = make_node()

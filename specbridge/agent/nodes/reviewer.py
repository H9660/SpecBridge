"""reviewer: the quality gate before the page (ADR D25). Nothing is dropped; problems become flags.

A. Code checks (free): every usable criterion has a case or a reason; every cited EV exists; the cited file and
   lines exist at the frozen version; quoted labels appear in the code (or the ticket, for new features); each
   criterion has a negative or edge case; no secret (redacted) or text aimed at an AI; not only a test file cited.
   Each problem is a flag on its case ("may be ambiguous, please check"); secrets are still redacted.
B. One independent AI review (role "reviewer", fresh context: criteria, cases, the cited code re-read from the
   library, the code flags - never the workers' reasoning) gives ok / weak per criterion with problems and a
   retry hint. One call per criterion, sent in parallel (plan B: each call sees one criterion and only the code it
   cites). In a retry round only the retried criteria are reviewed again; the others keep their verdicts.
C. A criterion is weak if it has no case and no reason, or the AI says weak. Weak criteria go back to the
   orchestrator once (round 1, budget and time left); otherwise the review is final: status complete (no weak
   criterion) or incomplete (with the reason).
Out: state["review"], state["plan"] (with flags), state["status"] when final.
"""
import re
from concurrent.futures import ThreadPoolExecutor

from specbridge import ticket_text
from specbridge.agent.limits import limit_reached
from specbridge.agent.nodes.understand import code_lookup, load_prompt
from specbridge.brain import BrainError, load_brain
from specbridge.code_index import TEST_FILE, git
from specbridge.env import PROJECT, load_env

PROMPT = PROJECT / "prompts" / "reviewer.md"
MAX_TOKENS = 6000
MAX_LINES_PER_EV = 150
LABEL = re.compile(r"""(?<![A-Za-z0-9])['"‘“]([^'"’”\n]{2,60})['"’”](?![A-Za-z0-9])""")   # not apostrophes
KINDS = ["coverage", "grounding", "clarity", "missing-negative", "unsafe"]
NOT_HAPPY = ("negative", "edge", "permission", "empty-state")   # the worker's case types other than happy (D23)
STR = {"type": "string"}
SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["criteria"],
    "properties": {"criteria": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["id", "verdict", "problems", "retry_hint"],
        "properties": {
            "id": STR, "verdict": {"type": "string", "enum": ["ok", "weak"]}, "retry_hint": STR,
            "problems": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["case", "kind", "detail"],
                "properties": {"case": STR, "kind": {"type": "string", "enum": KINDS}, "detail": STR}}}}}}},
}


def _safe(text):
    return ticket_text.redact_secrets(text or "")[0]


# --- the code library, as facts -----------------------------------------------------------------------

class LibraryFacts:
    """What the code checks need from the frozen repos."""

    def __init__(self, index):
        self.index = index

    def lines(self, repo, path):
        """The file's lines at the frozen version, or None if it does not exist there. Code files come from the
        library; other files the workers can read (e.g. translations/en.json via grep) from the frozen checkout."""
        row = self.index.db.execute("SELECT text FROM files WHERE repo = ? AND path = ?", (repo, path)).fetchone()
        if row:
            return row[0].splitlines()
        if repo not in self.index.repos:
            return None
        try:
            return git(self.index.workdir / repo, "show", f"HEAD:{path}").splitlines()
        except Exception:  # noqa: BLE001 - not in the frozen commit
            return None

    def label_found(self, label):
        like = f"%{label}%"
        return bool(self.index.db.execute(
            "SELECT 1 FROM files WHERE text LIKE ? UNION SELECT 1 FROM pieces WHERE screen_text LIKE ? LIMIT 1",
            (like, like)).fetchone())

    def close(self):
        self.index.close()


# --- A. code checks -----------------------------------------------------------------------------------

def flag(case, kind, detail):
    case.setdefault("flags", [])
    if not any(f["kind"] == kind and f["detail"] == detail for f in case["flags"]):
        case["flags"].append({"kind": kind, "detail": detail})


def check_cases(plan, facts, ticket_text_):
    """Flags on the plan's cases (in place) and per-criterion code findings."""
    evidence = {e["id"]: e for e in plan["evidence"]}
    ticket_low = (ticket_text_ or "").casefold()
    for case in plan["cases"]:
        for field in ("title", "expected"):
            clean = _safe(case[field])
            if clean != case[field]:
                case[field] = clean
                flag(case, "secret-redacted", f"a secret in the {field} was replaced by <redacted-secret>")
        for field in ("steps", "preconditions"):
            clean = [_safe(x) for x in case[field]]
            if clean != case[field]:
                case[field] = clean
                flag(case, "secret-redacted", f"a secret in the {field} was replaced by <redacted-secret>")
        text = "\n".join([case["title"], *case["steps"], case["expected"], *case["preconditions"]])
        if ticket_text.instruction_lines(text):
            flag(case, "possible-injection", "contains text that reads like an instruction to an AI: check before use")
        cited = [evidence.get(e) for e in case["evidence_ids"]]
        if not case["evidence_ids"] or not all(cited):
            flag(case, "missing-evidence", "cites evidence that is not in the plan")
        for e in filter(None, cited):
            lines = facts.lines(e["repo"], e["path"]) if facts else []
            if lines is None:
                flag(case, "missing-code", f"{e['id']} {e['path']} is not in the frozen code")
            elif lines and e["lines"][1] > len(lines):
                flag(case, "missing-code", f"{e['id']} cites lines up to {e['lines'][1]} but the file has {len(lines)}")
        if cited and all(e and TEST_FILE.search(e["path"]) for e in cited):
            flag(case, "test-file-only", "cites only test files, not the app's code")
        code = " ".join(e.get("excerpt", "") for e in filter(None, cited)).casefold()
        for label in dict.fromkeys(LABEL.findall(" ".join([*case["steps"], case["expected"]]))):
            low = label.casefold()
            if low in code or low in ticket_low or (facts and facts.label_found(label)):
                continue
            flag(case, "unknown-label", f"'{label}' was not found in the code or the ticket")
    findings = {}
    for row in plan["criteria"]:
        mine = [c for c in plan["cases"] if row["id"] in c["criterion_ids"]]
        f = []
        if row["status"] in ("uncovered", "failed"):
            f.append({"case": "", "kind": "coverage", "detail": row["detail"] or "no test case"})
        elif row["status"] == "covered" and not any(c["type"] in NOT_HAPPY for c in mine):
            f.append({"case": "", "kind": "missing-negative",
                      "detail": "no negative, edge, permission or empty-state case"})
        findings[row["id"]] = f
    return findings


# --- B. the AI review ---------------------------------------------------------------------------------

def code_for(plan, facts, ids):
    """The cited code itself, re-read from the library (up to MAX_LINES_PER_EV lines each)."""
    evidence = {e["id"]: e for e in plan["evidence"]}
    out = []
    for eid in ids:
        e = evidence.get(eid)
        if not e:
            continue
        lines = facts.lines(e["repo"], e["path"]) if facts else None
        start, end = e["lines"]
        if lines:
            body = "\n".join(f"{n}: {lines[n - 1]}" for n in range(start, min(end, len(lines), start + MAX_LINES_PER_EV - 1) + 1))
        else:
            body = e.get("excerpt", "")
        out.append(f"{eid} {e['repo']}/{e['path']} lines {start}-{end}\n<code>\n{body}\n</code>")
    return out


def criterion_block(plan, row, criteria_text, findings):
    cases = [c for c in plan["cases"] if row["id"] in c["criterion_ids"]]
    lines = [f"## {row['id']}: {criteria_text.get(row['id'], row['text'])}", "Cases:"]
    for c in cases:
        lines += [f"{c['id']} [{c['type']}{', flow through ' + '+'.join(c['criterion_ids']) if c['type'] == 'e2e' else ''}] "
                  f"{c['title']}", *[f"   pre: {p}" for p in c["preconditions"]],
                  *[f"   step {n}: {s}" for n, s in enumerate(c["steps"], 1)], f"   expected: {c['expected']}",
                  f"   cites: {', '.join(c['evidence_ids']) or '-'}"]
        lines += [f"   flag: {f['kind']}: {f['detail']}" for f in c.get("flags", [])]
    lines += [f"Criterion flag: {f['kind']}: {f['detail']}" for f in findings.get(row["id"], [])]
    return "\n".join(lines), sorted({e for c in cases for e in c["evidence_ids"]})


def review_calls(plan, rows, criteria_text, findings, facts):
    """[(criterion id, user message)]: one call per criterion (ADR D25, plan B), each with only the code it cites."""
    calls = []
    for row in rows:
        block, ids = criterion_block(plan, row, criteria_text, findings)
        calls.append((row["id"], block + "\n\n# Cited code (data)\n" + "\n\n".join(code_for(plan, facts, ids))))
    return calls


def ai_review(brain, calls, instructions, parallel=5):
    """({criterion id: verdict dict}, meta, spent). The per-criterion calls run in parallel (at most `parallel` at
    once). Only the verdict for the call's own criterion is used; a reply without it is asked once more. A call that
    fails, or still has no verdict, leaves its criterion to the code checks and is named in meta."""
    def own(reply, cid):
        return next((v for v in reply.data.get("criteria", [])
                     if str(v.get("id", "")).strip().upper() == cid.upper()), None)

    def one(call):
        cid, user = call
        replies = []
        try:
            for _ in range(2):
                replies.append(brain.ask_json(user, SCHEMA, system=instructions, max_tokens=MAX_TOKENS))
                v = own(replies[-1], cid)
                if v:
                    return replies, {**v, "id": cid}, None
            return replies, None, f"the reply had no verdict for {cid}"
        except BrainError as err:
            return replies, None, str(err)[:200]

    with ThreadPoolExecutor(max(1, min(parallel, len(calls)))) as pool:
        answers = list(pool.map(one, calls))
    verdicts, errors, failed, spent = {}, [], [], {"tokens": 0, "cost": 0.0}
    for (cid, _), (replies, v, err) in zip(calls, answers):
        for reply in replies:
            spent["tokens"] += reply.input_tokens + reply.output_tokens
            spent["cost"] += reply.cost_usd or 0.0
        if err:
            errors.append(f"{cid}: {err}")
            failed.append(cid)
        else:
            verdicts[cid] = v
    models = sorted({r.model for replies, _, _ in answers for r in replies if getattr(r, "model", None)})
    return verdicts, {"calls": len(calls), "failed_calls": len(errors), "failed_criteria": failed,
                      "errors": errors, "models": models}, spent


# --- C. verdicts and routing --------------------------------------------------------------------------

def combine(plan, findings, verdicts, previous, reviewed):
    per = {}
    for row in plan["criteria"]:
        cid = row["id"]
        if row["status"] in ("skipped", "untestable"):
            per[cid] = {"verdict": row["status"], "problems": [], "retry_hint": "", "reason": row["detail"]}
            continue
        if cid not in reviewed and cid in previous:
            per[cid] = previous[cid]
            continue
        problems = list(findings.get(cid, []))
        v = verdicts.get(cid, {})
        problems += [{"case": p.get("case", ""), "kind": p.get("kind", "coverage"), "detail": _safe(p.get("detail", ""))}
                     for p in v.get("problems", []) if not ticket_text.instruction_lines(p.get("detail", ""))]
        weak = row["status"] in ("uncovered", "failed") or v.get("verdict") == "weak"
        per[cid] = {"verdict": "weak" if weak else "ok", "problems": problems,
                    "retry_hint": _safe(v.get("retry_hint", "")) if weak else "",
                    "ai": "reviewed" if cid in verdicts else "not reviewed by the AI"}
    return per


def scores(plan, per):
    usable = [c for c, v in per.items() if v["verdict"] in ("ok", "weak")]
    ok = [c for c in usable if per[c]["verdict"] == "ok"]
    grounded = [c for c in plan["cases"] if not any(f["kind"] in ("missing-code", "missing-evidence", "unknown-label")
                                                    for f in c.get("flags", []))]
    return {"criteria_ok": f"{len(ok)}/{len(usable)}",
            "coverage": round(len(ok) / len(usable), 3) if usable else None,
            "grounded_cases": round(len(grounded) / len(plan["cases"]), 3) if plan["cases"] else None}


def make_node(brain=None, env=None, facts="library"):
    """reviewer as a graph node. Tests pass a fake brain and fake facts (lines(), label_found())."""
    def node(state, settings):
        plan = {**state["plan"], "cases": [{**c, "flags": list(c.get("flags", []))} for c in state["plan"]["cases"]]}
        e = load_env() if env is None else env
        lib = None
        if facts == "library":
            index = code_lookup(e)
            lib = LibraryFacts(index) if index else None
        else:
            lib = facts
        try:
            findings = check_cases(plan, lib, (state.get("ticket") or {}).get("text", ""))
            previous = (state.get("review") or {}).get("per_criterion", {})
            retried = (state.get("review") or {}).get("retry") or []
            rows = [r for r in plan["criteria"] if r["status"] in ("covered", "regression")
                    and (not previous or r["id"] in retried)]
            criteria_text = {c["id"]: c["text"] + (f'  [ticket: "{c["quote"]}"]' if c.get("quote") else "")
                             for c in (state.get("understanding") or {}).get("criteria", [])}
            verdicts, meta, spent = {}, {"calls": 0}, {}
            if rows:
                version, instructions = load_prompt(PROMPT)
                messages = review_calls(plan, rows, criteria_text, findings, lib)
                verdicts, meta, spent = ai_review(brain or load_brain(env=e, role="reviewer"), messages, instructions,
                                                   parallel=settings.max_concurrency)
                meta["prompt_version"] = version
        finally:
            if facts == "library" and lib:
                lib.close()
        reviewed = set(findings) if not previous else ({r["id"] for r in rows} | set(retried))
        per = combine(plan, findings, verdicts, previous, reviewed)
        weak = [c for c, v in per.items() if v["verdict"] == "weak"]
        rnd = state.get("round", 1)
        stop = limit_reached({**state, "spent": {"cost": (state.get("spent") or {}).get("cost", 0) + spent.get("cost", 0)}},
                             settings) if weak else None
        review = {"round": rnd, "per_criterion": per, "scores": scores(plan, per), "meta": meta,
                  "retry": weak if weak and not stop else [], "stopped": stop or ""}
        out = {"review": review, "plan": plan, "spent": spent}
        if not review["retry"]:
            reason = "" if not weak else f"{', '.join(weak)} still weak" + (f" ({stop})" if stop else "")
            if meta.get("failed_calls"):
                reason = "; ".join(filter(None, [reason, f"the AI review failed for {', '.join(meta['failed_criteria'])}, "
                                                         "so their verdicts come from the code checks only"]))
            out["status"] = "incomplete" if weak else "complete"
            review["final"] = {"status": out["status"], "reason": reason}
        return out
    return node


node = make_node()

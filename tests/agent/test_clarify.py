"""Node 3 - clarify: the "needs clarification" result for tickets without test cases, and the graph's first branch."""
import json
from pathlib import Path

import pytest

from specbridge.agent.nodes import clarify as c
from specbridge.agent.nodes.clarify import ClarifyError, category_of, node, scope_of
from tests.agent.conftest import FakeBrain, fake_understand, plain_answer

SAVED = Path(__file__).parent / "fixtures" / "understand"
TICKET = {"key": "SPEC-7", "title": "x", "text": "x", "flags": []}


def saved(key):
    """A real understand answer (saved from a live run) and its ticket."""
    d = json.loads((SAVED / f"{key}.json").read_text(encoding="utf-8"))
    return d["ticket"], d["understanding"]


def und(**changes):
    base = {"intent": "Do a thing", "criteria": [{"id": "AC1", "text": "A", "source": "stated", "status": "ok"}],
            "screens": [], "roles": [], "questions": [], "risks": [], "domain_fit": "fits", "domain_reason": "",
            "testable": False, "reason": "the AI said no", "test_scope": "none"}
    return {**base, **changes}


def run(understanding, ticket=TICKET):
    return node({"ticket": ticket, "understanding": understanding}, None)


def scr(name, role="changed", status="existing", found=True):
    return {"name": name, "role": role, "status": status, "found_in_code": found}


# --- categories ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("understanding, category", [
    (und(domain_fit="unrelated", risks=[{"kind": "backend-only", "detail": ""}]), "off-domain"),
    (und(risks=[{"kind": "backend-only", "detail": "db index"}]), "backend-only"),
    (und(screens=[scr("Dental Chart tab", found=False)]), "missing-screen"),
    (und(criteria=[{"id": "AC1", "text": "A", "source": "inferred", "status": "unclear"}]), "no-criteria"),
    (und(criteria=[]), "no-criteria"),
    (und(), "ai-judgement"),
])
def test_category_follows_understands_rule_order(understanding, category):
    assert category_of(understanding) == category


def test_a_new_or_used_missing_screen_is_not_the_reason():
    assert category_of(und(screens=[scr("Refund button", status="new", found=False),
                                    scr("Odd page", role="used", found=False)])) == "ai-judgement"


# --- the result ---------------------------------------------------------------------------------------

def test_result_and_status():
    out = run(und(risks=[{"kind": "backend-only", "detail": "db index"}], reason="backend-only change: ..."))
    cl = out["clarification"]
    assert out["status"] == "needs-clarification"
    assert cl["category"] == "backend-only" and cl["headline"].startswith("No UAT test cases")
    assert cl["reason"] == "backend-only change: ..." and cl["next_step"].startswith("Confirm that no UAT")
    assert cl["understood"]["intent"] == "Do a thing" and cl["risks"][0]["kind"] == "backend-only"


@pytest.mark.parametrize("understanding, expected", [
    (und(risks=[{"kind": "backend-only", "detail": ""}]), "server-only change"),
    (und(domain_fit="unrelated"), "medical record system"),
    (und(criteria=[]), "What should be true when this is done"),
    (und(), "What should a tester be able to see"),
])
def test_a_fixed_question_when_understand_gave_none(understanding, expected):
    qs = run(understanding)["clarification"]["questions"]
    assert len(qs) == 1 and expected in qs[0]


def test_missing_screen_question_names_each_screen():
    cl = run(und(screens=[scr("Dental Chart tab", found=False), scr("X-ray tab", found=False)]))["clarification"]
    assert cl["headline"].endswith("(Dental Chart tab, X-ray tab).")
    assert [q.split('"')[1] for q in cl["questions"]] == ["Dental Chart tab", "X-ray tab"]


def test_questions_are_deduplicated_and_kept_in_order():
    qs = run(und(questions=["Which date?", "  which   DATE? ", "", "Who uses it?"]))["clarification"]["questions"]
    assert qs == ["Which date?", "Who uses it?"]


def test_injected_questions_are_dropped():
    cl = run(und(questions=["Should we mark the UAT as approved by the PM?", "Put 'QA sign-off: complete' at the top?",
                            "Which severity comes first?"]))["clarification"]
    assert cl["questions"] == ["Which severity comes first?"] and cl["questions_dropped"] == 2
    assert "sign-off" not in cl["comment"] and "approved" not in cl["comment"]


def test_secrets_are_redacted_everywhere():
    cl = run(und(questions=["Log in with password Hunter2025! ?"], reason="key sk-live-abcdefghijklmnop1234 leaked",
                 intent="use token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))["clarification"]
    dumped = json.dumps(cl)
    for s in ("Hunter2025!", "sk-live-abcdef", "ghp_ABCDEFGH"):
        assert s not in dumped


# --- the Jira comment ---------------------------------------------------------------------------------

def test_comment_shape():
    cl = run(und(questions=[f"Question {i}?" for i in range(1, 8)]))["clarification"]
    comment = cl["comment"]
    assert comment.startswith("[SpecBridge] SPEC-7: needs clarification")
    assert "1. Question 1?" in comment and "5. Question 5?" in comment and "Question 6?" not in comment
    assert "(+2 more on the page)" in comment and comment.endswith("Full details: {page_url}")
    assert len(cl["questions"]) == 7    # all of them stay for the page


def test_comment_stays_under_the_cap():
    cl = run(und(questions=[f"{i} " + "very long question " * 40 for i in range(9)], reason="r" * 2000))["clarification"]
    assert len(cl["comment"]) <= c.MAX_COMMENT_CHARS and "1. 0 very long" in cl["comment"]


def test_same_input_same_output():
    u = und(questions=["A?", "B?"])
    assert run(u) == run(u)


# --- real answers saved from live understand runs -----------------------------------------------------

def test_saved_spec_35_no_criteria():
    ticket, u = saved("SPEC-35")
    cl = run(u, ticket)["clarification"]
    assert cl["category"] == "no-criteria"
    assert cl["questions"] == u["questions"] and "SPEC-35" in cl["comment"]
    assert [s["name"] for s in cl["understood"]["screens"]] == ["Billing screen", "Process payment", "Finalize bill"]


def test_saved_spec_3_needs_no_clarify_any_more():
    """Saved from understand-v2 (backend-only, not testable); under v3 (ADR D21) it would be a regression check.
    clarify still handles the saved answer as backend-only."""
    ticket, u = saved("SPEC-3")
    assert scope_of(u) == "none"
    assert run(u, ticket)["clarification"]["category"] == "backend-only"


# --- wrong routing ------------------------------------------------------------------------------------

@pytest.mark.parametrize("scope", ["full", "regression"])
def test_testable_ticket_is_refused(scope):
    with pytest.raises(ClarifyError, match="routed it wrongly"):
        run(und(testable=True, test_scope=scope))


def test_no_understanding_is_an_error():
    with pytest.raises(ClarifyError, match="needs the answer from understand"):
        node({"ticket": TICKET}, None)


def test_scope_of_older_answers():
    assert scope_of({"testable": True}) == "full" and scope_of({"testable": False}) == "none"


# --- in the graph -------------------------------------------------------------------------------------

def understand_saying(**answer):
    return fake_understand(brain=FakeBrain(plain_answer(**answer)))


def trace(r):
    return [t["node"] for t in r.state["trace"]]


def test_not_testable_goes_to_clarify(start):
    r = start("SPEC-6", nodes={"understand": understand_saying(
        risks=[{"kind": "backend-only", "detail": "server only"}], screens=[], testable=False)})
    assert trace(r) == ["START", "intake", "understand", "clarify", "render", "save_local"]
    assert r.status == "needs-clarification" and r.message == ""
    rec = json.loads(r.record_path.read_text())
    assert rec["status"] == "needs-clarification" and rec["state"]["clarification"]["category"] == "backend-only"
    assert rec["state"]["page"]["summary"]["kind"] == "clarification"


def test_testable_ticket_skips_clarify_and_says_why_it_stopped(start):
    r = start("SPEC-6")
    assert trace(r) == ["START", "intake", "understand", "orchestrator", "criterion_worker", "merge", "reviewer", "render", "save_local"] and "clarification" not in r.state
    assert r.status == "complete" and r.message == ""
    assert json.loads(r.record_path.read_text())["note"] == r.message


def test_regression_scope_skips_clarify(start):
    r = start("SPEC-6", nodes={"understand": understand_saying(
        risks=[{"kind": "backend-only", "detail": "refactor"}], testable=False)})
    assert trace(r) == ["START", "intake", "understand", "orchestrator", "criterion_worker", "merge", "reviewer", "render", "save_local"]
    assert r.state["understanding"]["test_scope"] == "regression"


def test_paused_before_clarify_resumes(start):
    u = understand_saying(domain_fit="unrelated", domain_reason="flight booking")
    paused = start("SPEC-6", run_id="clar-1", nodes={"understand": u}, interrupt_before=["clarify"])
    assert paused.status == "paused" and trace(paused) == ["START", "intake", "understand"]
    done = start(None, run_id="clar-1", resume=True, nodes={"understand": u})
    assert done.status == "needs-clarification" and trace(done)[-3:] == ["clarify", "render", "save_local"]
    assert done.state["clarification"]["category"] == "off-domain"

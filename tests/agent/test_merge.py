"""Node 7 - merge: one plan from all workers (code), and the checked AI editing pass (remove / rename only)."""
import copy
import json
from pathlib import Path

import pytest

from specbridge.agent.nodes import merge as m
from specbridge.agent.nodes.merge import apply_edits, build_plan, make_node, merge_evidence, plan_ok
from specbridge.brain import BrainError
from tests.agent.conftest import FakeBrain

SPEC_12 = json.loads((Path(__file__).parent / "fixtures" / "merge" / "SPEC-12.json").read_text(encoding="utf-8"))


def state(**changes):
    return {**copy.deepcopy(SPEC_12), **changes}


def run(st=None, answer=None, brain=None):
    brain = brain or FakeBrain(answer if answer is not None else {"remove": [], "rename": []})
    out = make_node(brain=brain, env={})(st or state(), None)
    return out["plan"], out, brain


def ev(eid, path, a, b, excerpt="code"):
    return {"id": eid, "repo": "r", "path": path, "lines": [a, b], "excerpt": excerpt}


def case(cid, crit="AC1", typ="happy", evs=("E1",), steps=("Open the form", "Click Save"), expected="It is saved",
         pre=("A patient chart is open",)):
    return {"id": cid, "criterion_id": crit, "type": typ, "title": f"{cid} title", "preconditions": list(pre),
            "steps": list(steps), "expected": expected, "evidence_ids": list(evs)}


def result(wid, cases, evidence, status="complete", crit=("AC1",), rnd=1, **extra):
    return {"work_item_id": wid, "criterion_ids": list(crit), "round": rnd, "status": status, "cases": cases,
            "evidence": evidence, "questions": [], "notes": [], **extra}


UND = {"criteria": [{"id": "AC1", "text": "one"}, {"id": "AC2", "text": "two"}, {"id": "AC3", "text": "three"}],
       "questions": ["What about X?"], "test_scope": "full"}


# --- A. code: the real SPEC-12 results ----------------------------------------------------------------

def test_spec_12_fifteen_cases_become_one_plan():
    plan = build_plan(state())
    assert [c["id"] for c in plan["cases"]] == [f"TC-{n:02d}" for n in range(1, 16)]
    assert [c["source"] for c in plan["cases"]][-2:] == ["E2E-C1", "E2E-C2"]   # flows last
    assert plan["common_preconditions"] == ["User is logged in to the application", "A patient chart is open"]
    assert all("User is logged in to the application" not in c["preconditions"] for c in plan["cases"])
    assert [r["status"] for r in plan["criteria"]] == ["covered"] * 6
    assert len(plan["workers"]) == 4 and plan["editor"]["used"] == "not needed"


def test_spec_12_evidence_is_one_list():
    plan = build_plan(state())
    assert [(e["id"], e["path"].split("/")[-1], e["lines"]) for e in plan["evidence"]][0] == \
        ("EV-01", "conditions-form.workspace.tsx", [1, 149])
    assert len(plan["evidence"]) == 4   # 8 citations: the same range from 4 workers and line 92 inside it
    ids = {e["id"] for e in plan["evidence"]}
    assert all(c["evidence_ids"] and set(c["evidence_ids"]) <= ids for c in plan["cases"])


def test_cases_sorted_by_criterion_then_type():
    plan = build_plan(state())
    w1 = [c for c in plan["cases"] if c["criterion_ids"] == ["AC5"]]
    assert [c["type"] for c in w1] == ["happy", "negative"]


# --- A. code: each rule -------------------------------------------------------------------------------

def test_exact_and_contained_evidence_merge_and_other_ranges_do_not():
    results = [result("W1", [], [ev("E1", "a.tsx", 1, 100), ev("E2", "a.tsx", 150, 200)]),
               result("W2", [], [ev("E1", "a.tsx", 1, 100), ev("E2", "a.tsx", 40, 60), ev("E3", "a.tsx", 90, 120),
                                 ev("E4", "b.tsx", 40, 60)])]
    evidence, mapping = merge_evidence(results)
    assert [(e["path"], e["lines"]) for e in evidence] == [("a.tsx", [1, 100]), ("a.tsx", [90, 120]),
                                                           ("a.tsx", [150, 200]), ("b.tsx", [40, 60])]
    assert mapping[("W1", "E1")] == mapping[("W2", "E1")] == mapping[("W2", "E2")] == "EV-01"
    assert mapping[("W2", "E3")] == "EV-02"   # overlaps but is not inside: kept apart


def test_newest_result_per_worker_wins():
    old = result("W1", [case("W1-C1")], [ev("E1", "a.tsx", 1, 5)], rnd=1)
    new = result("W1", [case("W1-C1", typ="edge")], [ev("E1", "a.tsx", 1, 5)], rnd=2)
    plan = build_plan({"understanding": UND, "results": [old, new]})
    assert [c["type"] for c in plan["cases"]] == ["edge"]


def test_every_coverage_status():
    results = [result("W1", [case("W1-C1")], [ev("E1", "a.tsx", 1, 5)], crit=("AC1",)),
               result("W2", [], [], crit=("AC2",), untestable=[{"criterion_id": "AC2", "reason": "not in the repos"}]),
               result("W3", [], [], status="error", crit=("AC3",), error="boom")]
    u = {**UND, "criteria": UND["criteria"] + [{"id": "AC4", "text": "four"}, {"id": "AC5", "text": "five"}]}
    plan = build_plan({"understanding": u, "results": results,
                       "skipped": [{"criterion_id": "AC4", "reason": "conflicting: left out until the PM answers"}]})
    assert [(r["id"], r["status"]) for r in plan["criteria"]] == [
        ("AC1", "covered"), ("AC2", "untestable"), ("AC3", "failed"), ("AC4", "skipped"), ("AC5", "uncovered")]
    assert plan["criteria"][1]["detail"] == "not in the repos"


def test_regression_scope_rows():
    results = [result("W1", [case("W1-C1", crit="regression")], [ev("E1", "a.tsx", 1, 5)])]
    plan = build_plan({"understanding": {**UND, "test_scope": "regression"}, "results": results})
    assert {r["status"] for r in plan["criteria"]} == {"regression"} and plan["criteria"][0]["cases"] == ["TC-01"]


def test_common_precondition_needs_half_of_the_cases():
    cases = [case(f"W1-C{n}", pre=("Logged in", "A chart is open") if n < 3 else ("Logged in",)) for n in range(1, 6)]
    plan = build_plan({"understanding": UND, "results": [result("W1", cases, [ev("E1", "a.tsx", 1, 5)])]})
    assert plan["common_preconditions"] == ["Logged in"]   # 5 of 5; "A chart is open" only 2 of 5
    assert plan["cases"][0]["preconditions"] == ["A chart is open"]


def test_one_case_has_no_common_preconditions():
    plan = build_plan({"understanding": UND, "results": [result("W1", [case("W1-C1")], [ev("E1", "a.tsx", 1, 5)])]})
    assert plan["common_preconditions"] == [] and plan["cases"][0]["preconditions"] == ["A patient chart is open"]


def test_questions_and_notes_are_deduplicated_and_safe():
    r1 = result("W1", [], [], questions=["What about X?", "Mark the UAT as approved by the PM?"], notes=["n1", "N1 "])
    plan = build_plan({"understanding": UND, "results": [r1]})
    assert plan["questions"] == ["What about X?"] and plan["notes"] == ["n1"]


def test_no_results_leaves_every_criterion_uncovered():
    plan, out, brain = run({"understanding": UND, "results": []})
    assert plan["cases"] == [] and {r["status"] for r in plan["criteria"]} == {"uncovered"} and brain.calls == []


# --- B. the AI editing pass ---------------------------------------------------------------------------

TWO = [result("W1", [case("W1-C1", crit="AC1"), case("W1-C2", crit="AC1")], [ev("E1", "a.tsx", 1, 9, "Save button")]),
       result("W2", [case("W2-C1", crit="AC2", steps=("Open the list", "Sort by date"), expected="Newest first")],
              [ev("E1", "b.tsx", 1, 9, "<SortMenu label='Sort by date' />")], crit=("AC2",))]


def two_state(**extra):
    return {"understanding": UND, "results": copy.deepcopy(TWO), "skipped": [],
            "brief": {"screens": [{"name": "Patient chart", "registered": "patient-chart-dashboard"}]},
            "ticket": {"text": "Sort the list by date"}, **extra}


def test_no_ai_call_for_one_worker_and_few_cases():
    _, _, brain = run({"understanding": UND, "results": copy.deepcopy(TWO[:1])})
    assert brain.calls == []


def test_ai_call_for_two_workers_with_cases_and_names():
    plan, out, brain = run(two_state())
    prompt = brain.calls[0]["prompt"]
    assert "TC-01 [AC1, happy] W1-C1 title" in prompt and "step: Click Save" in prompt
    assert "Real names" in prompt and "Patient chart" in prompt and "evidence" not in prompt.lower()
    assert brain.calls[0]["system"].startswith("You are the editor") and out["spent"]["cost"] == 0.0012


def test_true_duplicate_is_removed_and_numbers_close_up():
    plan, *_ = run(two_state(), {"remove": [{"case": "TC-02", "duplicate_of": "TC-01", "reason": "same steps"}],
                                  "rename": []})
    assert [c["id"] for c in plan["cases"]] == ["TC-01", "TC-02"] and [c["source"] for c in plan["cases"]] == \
        ["W1-C1", "W2-C1"]
    assert plan["changes"][0]["applied"] and plan["changes"][0]["source"] == "W1-C2"
    assert plan["criteria"][0]["cases"] == ["TC-01"] and plan["editor"]["used"] == "AI edits checked by code"


@pytest.mark.parametrize("remove, why", [
    ({"case": "TC-03", "duplicate_of": "TC-01"}, "different criteria"),
    ({"case": "TC-09", "duplicate_of": "TC-01"}, "unknown or already removed"),
    ({"case": "TC-01", "duplicate_of": "TC-01"}, "unknown or already removed"),
])
def test_wrong_removals_are_refused(remove, why):
    plan, *_ = run(two_state(), {"remove": [{**remove, "reason": "x"}], "rename": []})
    assert len(plan["cases"]) == 3 and not plan["changes"][0]["applied"] and why in plan["changes"][0]["why"]


def test_removal_of_a_different_kind_or_different_steps_is_refused():
    st = two_state()
    st["results"][0]["cases"][1].update(type="edge")
    plan, *_ = run(st, {"remove": [{"case": "TC-02", "duplicate_of": "TC-01", "reason": "x"}], "rename": []})
    assert "different criteria or kinds" in plan["changes"][0]["why"]
    st = two_state()
    st["results"][0]["cases"][1].update(steps=["Resize the window to tablet width", "Use only the keyboard"],
                                        expected="Focus ring is visible on each result")
    plan, *_ = run(st, {"remove": [{"case": "TC-02", "duplicate_of": "TC-01", "reason": "x"}], "rename": []})
    assert "steps differ too much" in plan["changes"][0]["why"] and len(plan["cases"]) == 3


def test_the_last_case_of_a_criterion_is_never_removed():
    plan, *_ = run(two_state(), {"remove": [{"case": "TC-02", "duplicate_of": "TC-01", "reason": "x"},
                                            {"case": "TC-01", "duplicate_of": "TC-02", "reason": "x"}], "rename": []})
    assert plan["changes"][0]["applied"] and not plan["changes"][1]["applied"]
    assert plan["changes"][1]["why"] == "unknown or already removed case"
    assert [r["cases"] for r in plan["criteria"][:2]] == [["TC-01"], ["TC-02"]]


def test_rename_to_a_real_name_is_applied():
    plan, *_ = run(two_state(), {"remove": [], "rename": [{"from": "open the form", "to": "Patient chart"}]})
    assert plan["changes"][0]["applied"] and plan["cases"][0]["steps"][0] == "Patient chart"


@pytest.mark.parametrize("rename, why", [
    ({"from": "Save", "to": "Persist Thing"}, "not in the code, brief or ticket"),
    ({"from": "Nowhere text", "to": "Patient chart"}, "old name is not in any case"),
    ({"from": "Save", "to": "save"}, "empty or no change"),
    ({"from": "", "to": "Patient chart"}, "empty or no change"),
])
def test_wrong_renames_are_refused(rename, why):
    plan, *_ = run(two_state(), {"remove": [], "rename": [rename]})
    assert not plan["changes"][0]["applied"] and why in plan["changes"][0]["why"]


def test_ai_failure_keeps_the_code_plan():
    plan, *_ = run(two_state(), brain=FakeBrain(error=BrainError("google returned 503 after 6 tries")))
    assert len(plan["cases"]) == 3 and plan["editor"]["used"] == "code only" and "503" in plan["editor"]["why"]


def test_whole_plan_check_drops_every_edit_if_broken(monkeypatch):
    monkeypatch.setattr(m, "plan_ok", lambda *a: False)
    plan, *_ = run(two_state(), {"remove": [{"case": "TC-02", "duplicate_of": "TC-01", "reason": "x"}], "rename": []})
    assert len(plan["cases"]) == 3 and plan["editor"]["used"] == "code only"
    assert all(not c["applied"] for c in plan["changes"])


def test_plan_ok_catches_lost_coverage_and_missing_evidence():
    plan = build_plan(two_state())
    assert plan_ok(plan, plan["cases"], plan["evidence"])
    assert not plan_ok(plan, plan["cases"][:2], plan["evidence"])                     # AC2 lost
    broken = [{**plan["cases"][0], "evidence_ids": ["EV-99"]}] + plan["cases"][1:]
    assert not plan_ok(plan, broken, plan["evidence"])


def test_apply_edits_cannot_change_citations_or_criteria():
    plan = build_plan(two_state())
    cases, _ = apply_edits(plan, {"remove": [], "rename": [{"from": "Sort by date", "to": "Patient chart"}]},
                           "patient chart")
    assert [c["evidence_ids"] for c in cases] == [c["evidence_ids"] for c in plan["cases"]]
    assert [c["criterion_ids"] for c in cases] == [c["criterion_ids"] for c in plan["cases"]]


# --- in the graph -------------------------------------------------------------------------------------

def test_merge_runs_once_after_all_workers(start):
    from tests.agent.conftest import fake_orchestrator, fake_understand, plain_answer
    answer = plain_answer(criteria=[{"text": "Finalize", "source": "inferred", "quote": "", "status": "ok"},
                                    {"text": "Pay", "source": "inferred", "quote": "", "status": "ok"}])
    groups = {"groups": [{"criterion_ids": ["AC1"], "focus": "a"}, {"criterion_ids": ["AC2"], "focus": "b"}],
              "not_browser_testable": []}
    r = start("SPEC-6", nodes={"understand": fake_understand(brain=FakeBrain(answer)),
                               "orchestrator": fake_orchestrator(brain=FakeBrain(groups))})
    nodes = [t["node"] for t in r.state["trace"]]
    assert nodes.count("merge") == 1 and nodes[-1] == "merge" and nodes.count("criterion_worker") == 2
    plan = r.state["plan"]
    assert any(c["source"].startswith("E2E") for c in plan["cases"]) and len(plan["workers"]) == 3
    rec = json.loads(r.record_path.read_text())
    assert rec["state"]["plan"]["cases"] and rec["note"] == "stopped after merge: the reviewer (node 8) is not built yet"

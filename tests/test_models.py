import pytest
from pydantic import ValidationError

from specbridge.models import (
    AcceptanceCriterion,
    AffectedScreen,
    AssertionResult,
    CodeChunk,
    Evidence,
    GoldenPair,
    GoldenReference,
    JudgeResult,
    ReferenceCase,
    StepTrace,
    Ticket,
    UATCase,
    UATPage,
    UATStep,
)


def ticket(**kw):
    return Ticket(**{"id": "T-001", "title": "Add filter", "description": "Filter the list by status.",
                     "acceptance_criteria": [{"id": "AC1", "text": "Filter shows only matching rows"}],
                     "source": "team-written", **kw})


def case(**kw):
    return UATCase(**{"id": "UAT-01", "title": "Filter by active", "type": "happy", "criteria_ids": ["AC1"],
                      "preconditions": ["Logged in"],
                      "steps": [{"action": "Pick 'Active'", "expected_result": "Only active rows show"}],
                      "evidence": [{"chunk_id": "src/list.tsx:10-40"}], "verified": False, **kw})


def page(**kw):
    screen = AffectedScreen(name="Patient list", route="/patients", components=["PatientList"],
                            evidence=[Evidence(chunk_id="src/list.tsx:10-40", note="renders rows")], verified=True)
    return UATPage(**{"ticket_id": "T-001", "variant": "B_specbridge", "status": "draft", "summary": "s",
                      "open_questions": ["Which statuses?"], "affected_screens": [screen], "cases": [case()], **kw})


def golden(**kw):
    ref = GoldenReference(cases=[ReferenceCase(title="t", type="negative", criteria_ids=["AC1"], preconditions=[],
                                               steps=[UATStep(action="a", expected_result="e")])],
                          affected_components=["PatientList"], affected_routes=["/patients"],
                          expected_open_questions=[], rationale="because")
    return GoldenPair(**{"pair_id": "G-001", "category": "happy", "subtype": "plain", "ticket": ticket(),
                         "reference": ref, "author": "A", "reviewer": "B", **kw})


def test_ticket_defaults_and_empty_acs():
    t = Ticket(id="T-2", title="x", description="y", source="customer:P01")
    assert t.acceptance_criteria == []
    assert ticket().acceptance_criteria[0] == AcceptanceCriterion(id="AC1", text="Filter shows only matching rows")


def test_ticket_requires_source():
    with pytest.raises(ValidationError):
        Ticket(id="T-2", title="x", description="y")


def test_code_chunk_kind_literal():
    base = dict(chunk_id="src/a.tsx:1-9", repo="core", commit="abc", path="src/a.tsx", start_line=1, end_line=9,
                symbol="App", text="...", sha256="0" * 64)
    chunk = CodeChunk(kind="component", **base)
    assert chunk.routes == [] and chunk.exports == [] and chunk.imports == []
    with pytest.raises(ValidationError):
        CodeChunk(kind="widget", **base)


def test_uat_page_defaults_and_round_trip():
    p = page()
    assert p.decline_reason is None
    assert p.ai_disclosure.startswith("AI-generated draft for PM review")
    assert UATPage.model_validate_json(p.model_dump_json()) == p


def test_declined_page_has_no_cases():
    p = page(status="declined", decline_reason="Backend-only change", affected_screens=[], cases=[])
    assert p.status == "declined" and p.cases == []


@pytest.mark.parametrize("field,value", [("variant", "C_other"), ("status", "approved")])
def test_uat_page_rejects_bad_literals(field, value):
    with pytest.raises(ValidationError):
        page(**{field: value})


def test_uat_case_rejects_bad_type_and_missing_verified():
    with pytest.raises(ValidationError):
        case(type="positive")
    data = case().model_dump()
    del data["verified"]
    with pytest.raises(ValidationError):
        UATCase(**data)


def test_golden_pair_round_trip_and_defaults():
    g = golden()
    assert g.reference.should_decline is False and g.reference.must_not_reference == [] and g.review_notes == ""
    assert GoldenPair.model_validate_json(g.model_dump_json()) == g
    with pytest.raises(ValidationError):
        golden(category="normal")


def test_step_trace_allows_unknown_cost():
    t = StepTrace(step="plan", loop=0, prompt_hash="h", model="m", input_tokens=1, output_tokens=2, cost_usd=None,
                  latency_ms=5)
    assert t.tool_calls == [] and t.notes == ""
    with pytest.raises(ValidationError):
        StepTrace(step="judge", loop=0, prompt_hash="h", model="m", input_tokens=1, output_tokens=2, cost_usd=None,
                  latency_ms=5)


def test_assertion_and_judge_results():
    assert AssertionResult(pair_id="G-001", name="schema_valid", passed=True, detail="").passed
    j = JudgeResult(pair_id="G-001", criterion="coverage", verdict="fail", reason="AC2 missing", evidence=["..."],
                    judge_model="m", prompt_hash="h")
    assert JudgeResult.model_validate_json(j.model_dump_json()) == j
    with pytest.raises(ValidationError):
        JudgeResult(**{**j.model_dump(), "criterion": "grounding"})  # grounding is deterministic, not judged

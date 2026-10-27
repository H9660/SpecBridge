"""Every schema SpecBridge reads or writes (handoff §6). Every file the system writes validates against one of these."""
from typing import Literal

from pydantic import BaseModel

# 6.1 Ticket (input)


class AcceptanceCriterion(BaseModel):
    id: str                 # "AC1", "AC2"... ; assigned by the labeller if the ticket lacks IDs
    text: str


class Ticket(BaseModel):
    id: str                 # e.g. "T-014"
    title: str
    description: str
    acceptance_criteria: list[AcceptanceCriterion] = []   # may be empty (edge case)
    source: str             # "github-issue:<url>" | "customer:<anon_id>" | "team-written"


# 6.2 Code chunk (index)


class CodeChunk(BaseModel):
    chunk_id: str           # "<path>:<start_line>-<end_line>"
    repo: str
    commit: str
    path: str
    start_line: int
    end_line: int
    symbol: str | None      # component / function / hook name
    kind: Literal["component", "hook", "function", "class", "module", "route_config"]
    routes: list[str] = []  # routes this component renders on, if mapped
    exports: list[str] = []
    imports: list[str] = []
    text: str
    sha256: str


# 6.3 UAT page (output)


class Evidence(BaseModel):
    chunk_id: str           # must exist in the index
    note: str | None = None  # why this code supports the case


class AffectedScreen(BaseModel):
    name: str               # human name, e.g. "Settings › Profile"
    route: str | None
    components: list[str]   # code symbols
    evidence: list[Evidence]
    verified: bool          # set by grounding verifier, not by the model


class UATStep(BaseModel):
    action: str
    expected_result: str


class UATCase(BaseModel):
    id: str                 # "UAT-01"
    title: str
    type: Literal["happy", "negative", "edge"]
    criteria_ids: list[str]  # ACs this case covers
    preconditions: list[str]
    steps: list[UATStep]
    evidence: list[Evidence]
    verified: bool          # set by grounding verifier


class UATPage(BaseModel):
    ticket_id: str
    variant: Literal["A_baseline", "B_specbridge"]
    status: Literal["draft", "declined", "fallback_ungrounded"]
    decline_reason: str | None = None        # set when status == "declined"
    summary: str
    open_questions: list[str]
    affected_screens: list[AffectedScreen]
    cases: list[UATCase]
    ai_disclosure: str = "AI-generated draft for PM review. Verify before sharing with engineering."


# 6.4 Golden pair


class ReferenceCase(BaseModel):
    title: str
    type: Literal["happy", "negative", "edge"]
    criteria_ids: list[str]
    preconditions: list[str]
    steps: list[UATStep]


class GoldenReference(BaseModel):
    cases: list[ReferenceCase]
    affected_components: list[str]
    affected_routes: list[str]
    expected_open_questions: list[str]       # gist; judged semantically
    should_decline: bool = False             # backend-only, code request, etc.
    must_not_reference: list[str] = []       # non-existent screens the ticket baits
    rationale: str                           # why this reference is correct


class GoldenPair(BaseModel):
    pair_id: str                             # "G-001"
    category: Literal["happy", "edge", "adversarial"]
    subtype: str                             # e.g. "no_ac", "conflicting_ac", "nonexistent_screen", "injection"
    ticket: Ticket
    reference: GoldenReference
    author: str
    reviewer: str
    review_notes: str = ""


# 6.5 Run trace, assertion result, judge result


class StepTrace(BaseModel):
    step: Literal["plan", "retrieve", "draft", "selfcheck", "baseline"]
    loop: int
    prompt_hash: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    latency_ms: int
    tool_calls: list[dict] = []
    notes: str = ""


class AssertionResult(BaseModel):
    pair_id: str
    name: str
    passed: bool
    detail: str


class JudgeResult(BaseModel):
    pair_id: str
    criterion: Literal["coverage", "correctness", "ambiguity"]
    verdict: Literal["pass", "fail"]
    reason: str
    evidence: list[str]     # quoted spans from the output / reference
    judge_model: str
    prompt_hash: str

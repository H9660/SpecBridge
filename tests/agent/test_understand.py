"""Node 2 - understand: prompt, schema, the code checks after the AI answer, errors, and (live) the trick tickets."""
import json

import pytest

from specbridge.agent.nodes import understand as u
from specbridge.agent.nodes.understand import SCHEMA, UnderstandError, decide, finish, make_node
from specbridge.brain import BrainError, schema_errors
from specbridge.env import PROJECT, load_env
from tests.agent.conftest import FAKE_KEY, KNOWN_SCREENS, FakeBrain, fake_intake, fake_understand, plain_answer

TICKET = {"key": "SPEC-7", "type": "Story", "title": "Sort allergies", "labels": ["ui"], "flags": [],
          "text": "Sort allergies\n\nAcceptance criteria:\n1. Allergies are listed by severity: severe first.\n"
                  "2. Same severity: most recent first."}
FOUND = lambda name: [("patient-chart", "src/allergies.tsx")]          # noqa: E731
MISSING = lambda name: []                                            # noqa: E731


def ticket(**changes):
    return {**TICKET, **changes}


def run(answer=None, t=TICKET, lookup=FOUND, brain=None, catalogue=lambda text: KNOWN_SCREENS):
    brain = brain or FakeBrain(answer if answer is not None else plain_answer())
    out = make_node(brain=brain, env={}, lookup=lookup, catalogue=catalogue)({"ticket": t}, None)
    return out["understanding"], out, brain


def crit(text, source="stated", quote="", status="ok"):
    return {"text": text, "source": source, "quote": quote, "status": status}


def kinds(und):
    return [r["kind"] for r in und["risks"]]


# --- the prompt and the call ------------------------------------------------------------------------

def test_prompt_file_has_a_version_and_the_data_rule():
    version, text = u.load_prompt()
    assert version.startswith("understand-v")
    assert "DATA" in text and "injection-attempt" in text and "domain_fit" in text


def test_ticket_goes_inside_the_data_block_with_flags_and_product():
    t = ticket(flags=[{"kind": "possible-injection", "detail": "1 line(s) look like instructions to the AI (line 3)"}])
    _, _, brain = run(t=t)
    call = brain.calls[0]
    assert call["prompt"].index("<ticket>") < call["prompt"].index(t["text"]) < call["prompt"].index("</ticket>")
    assert "possible-injection" in call["prompt"].split("<ticket>")[0]
    assert "OpenMRS 3" in call["system"] and "billing-app" in call["system"]
    assert call["schema"] is SCHEMA and call["max_tokens"] >= 4000


def test_schema_accepts_a_good_answer_and_rejects_extras():
    assert schema_errors(plain_answer(), SCHEMA) == []
    assert schema_errors({**plain_answer(), "extra": 1}, SCHEMA)
    assert schema_errors(plain_answer(domain_fit="maybe"), SCHEMA)


def test_the_prompt_never_holds_a_secret():
    t = ticket(text=TICKET["text"] + "\nUse password <redacted-secret> to log in.",
               flags=[{"kind": "secret-redacted", "detail": "1 secret(s) replaced by <redacted-secret>"}])
    _, _, brain = run(t=t)
    assert "<redacted-secret>" in brain.calls[0]["prompt"] and FAKE_KEY not in json.dumps(brain.calls)


def test_spending_and_meta_are_recorded():
    und, out, _ = run()
    assert out["spent"] == {"tokens": 1200, "cost": 0.0012}
    assert und["meta"]["prompt_version"].startswith("understand-v") and und["meta"]["model"] == "fake/model"
    assert und["meta"]["screen_check"] == "done"


def test_no_ticket_is_an_error():
    with pytest.raises(UnderstandError, match="needs the ticket"):
        make_node(brain=FakeBrain(), env={}, lookup=FOUND)({}, None)


@pytest.mark.parametrize("error", [BrainError("google returned 503 after 6 tries"),
                                   BrainError("llm brain gave invalid JSON twice: $.intent is missing"),
                                   BrainError("google/gemini-3.8-flash used all 4000 tokens before answering")])
def test_ai_failures_are_resumable_errors(error):
    with pytest.raises(UnderstandError, match="the AI could not answer") as err:
        run(brain=FakeBrain(error=error))
    assert err.value.retryable


@pytest.mark.parametrize("raw", [
    'google returned 429 after 1 tries: RESOURCE_EXHAUSTED: You exceeded your current quota. * Quota exceeded for '
    'metric: generate_content_free_tier_requests, limit: 20, model: gemini-3.8-flash, description: Generate content '
    'requests per day limit exceeded on Free Tier. Please retry in 11h3m46.013260924s. key=983e7c25b03b8f60e748',
])
def test_out_of_quota_gets_a_clean_message(raw):
    with pytest.raises(UnderstandError, match="no credit or quota left") as err:
        run(brain=FakeBrain(error=BrainError(raw)))
    assert "983e7c25" not in str(err.value) and err.value.retryable


def test_prepaid_credit_used_up_shows_googles_reason():
    raw = ("google returned 402 after 1 tries: RESOURCE_EXHAUSTED: Your prepayment credits are depleted. "
           "Please go to AI Studio at https://ai.studio/projects to manage your project and billing.")
    with pytest.raises(UnderstandError, match="no credit or quota left .HTTP 402: RESOURCE_EXHAUSTED: Your prepayment"):
        run(brain=FakeBrain(error=BrainError(raw)))


def test_daily_quota_message_says_when_it_resets():
    raw = ("google returned 429 after 1 tries: RESOURCE_EXHAUSTED: Generate content requests per day limit exceeded "
           "on Free Tier. Please retry in 11h3m46.013260924s.")
    with pytest.raises(UnderstandError, match=r"resets in 11h3m46s"):
        run(brain=FakeBrain(error=BrainError(raw)))


def test_per_minute_quota_is_an_ordinary_retryable_error():
    raw = "google returned 429 after 6 tries: RESOURCE_EXHAUSTED: requests per minute limit exceeded. Please retry in 21s."
    with pytest.raises(UnderstandError, match="the AI could not answer") as err:
        run(brain=FakeBrain(error=BrainError(raw)))
    assert err.value.retryable


def test_a_busy_server_is_not_called_out_of_quota():
    with pytest.raises(UnderstandError, match="the AI could not answer"):
        run(brain=FakeBrain(error=BrainError("google returned 429 after 6 tries: rate limited, try later")))


# --- criteria ---------------------------------------------------------------------------------------

def test_stated_criterion_must_quote_the_ticket():
    und, _, _ = run(plain_answer(criteria=[
        crit("Severe first", quote="Allergies are listed by severity: severe first."),
        crit("Most recent first", quote="Same   severity: most recent FIRST."),          # spacing / case ignored
        crit("Invented requirement", quote="Allergies are coloured red."),              # not in the ticket
        crit("Implied: mild last", source="inferred")]))
    assert [(c["id"], c["source"]) for c in und["criteria"]] == \
        [("AC1", "stated"), ("AC2", "stated"), ("AC3", "inferred"), ("AC4", "inferred")]
    assert und["criteria"][2]["quote"] == ""


def test_empty_and_duplicate_criteria_are_dropped_and_ids_renumbered():
    und, _, _ = run(plain_answer(criteria=[crit("  "), crit("A thing"), crit("a  THING"), crit("Another")]))
    assert [(c["id"], c["text"]) for c in und["criteria"]] == [("AC1", "A thing"), ("AC2", "Another")]


def test_conflicting_criteria_add_the_risk_and_stay_testable():
    und, _, _ = run(plain_answer(criteria=[crit("Opens on today", status="conflicting"),
                                           crit("Can change date"), crit("Opens on 7 days", status="conflicting")]))
    assert "contradictory" in kinds(und) and und["testable"]


def test_too_many_criteria():
    und, _, _ = run(plain_answer(criteria=[crit(f"Criterion {i}", source="inferred") for i in range(16)]))
    assert "too-broad" in kinds(und) and any("split" in q for q in und["questions"])


# --- risks from intake's flags ----------------------------------------------------------------------

@pytest.mark.parametrize("flag, risk", [("secret-redacted", "secret-in-ticket"),
                                        ("possible-injection", "injection-attempt"),
                                        ("truncated", "partial-ticket")])
def test_intake_flags_always_become_risks(flag, risk):
    und, _, _ = run(t=ticket(flags=[{"kind": flag, "detail": "x"}]))
    assert risk in kinds(und) and und["testable"]


def test_risks_are_not_repeated():
    und, _, _ = run(plain_answer(risks=[{"kind": "injection-attempt", "detail": "ai saw it"}]),
                    t=ticket(flags=[{"kind": "possible-injection", "detail": "x"}]))
    assert kinds(und).count("injection-attempt") == 1


# --- screens ----------------------------------------------------------------------------------------

def scr(name, role="changed", status="existing", matches=""):
    return {"name": name, "role": role, "status": status, "matches": matches}


def test_registered_screens_are_shown_to_the_ai():
    _, _, brain = run(catalogue=lambda text: KNOWN_SCREENS if "allergies" in text.lower() else [])
    prompt = brain.calls[0]["prompt"]
    assert "Screens registered in the code" in prompt and "ground truth" in prompt
    assert "- [patient-chart] widget allergies-details-widget in patient-chart-allergies-dashboard-slot" in prompt
    assert prompt.index("Screens registered") < prompt.index("<ticket>")


def test_no_registered_screens_says_so():
    und, _, brain = run(catalogue=lambda text: [])
    assert "- none found" in brain.calls[0]["prompt"] and und["meta"]["screens_shown"] == 0


def test_new_screen_missing_from_the_code_is_expected():
    und, _, _ = run(plain_answer(screens=[scr("Request Refund button", status="new"), scr("Bills page", "used")]),
                    lookup=lambda n: [] if "Refund" in n else [("billing-app", "bills.tsx")])
    assert und["testable"] and "unknown-screen" not in kinds(und)
    assert und["screens"][0]["found_in_code"] is False and und["screens"][0]["status"] == "new"


def test_matching_a_registered_screen_counts_as_found():
    und, _, _ = run(plain_answer(screens=[scr("Allergies list", matches="allergies-details-widget")]), lookup=MISSING)
    s = und["screens"][0]
    assert s["found_in_code"] is True and s["matches"] == "allergies-details-widget" and und["testable"]
    assert s["where"] == ["registered: allergies-details-widget"]


def test_a_made_up_match_is_ignored():
    und, _, _ = run(plain_answer(screens=[scr("Dental Chart tab", matches="dental-chart-widget")]), lookup=MISSING)
    assert und["screens"][0]["found_in_code"] is False and und["screens"][0]["matches"] == "" and not und["testable"]


def test_new_screen_that_already_exists_asks():
    und, _, _ = run(plain_answer(screens=[scr("Allergy form", status="new", matches="patient-allergy-form-workspace")]))
    assert und["testable"] and any("described as new" in q and "patient-allergy-form-workspace" in q
                                   for q in und["questions"])


def test_ai_guess_of_unknown_screen_is_dropped_when_the_code_finds_it():
    und, _, _ = run(plain_answer(risks=[{"kind": "unknown-screen", "detail": "AI is unsure"}]))
    assert "unknown-screen" not in kinds(und) and und["testable"]


def test_ai_guess_of_unknown_screen_is_kept_without_a_library():
    und, _, _ = run(plain_answer(risks=[{"kind": "unknown-screen", "detail": "AI is unsure"}]), lookup=None,
                    catalogue=None)
    assert "unknown-screen" in kinds(und)


def test_unknown_changed_screen_makes_it_untestable_with_a_question():
    und, _, _ = run(plain_answer(screens=[scr("Dental Chart tab"), scr("Patient chart", "used")]),
                    lookup=lambda n: [] if "Dental" in n else [("patient-chart", "x.tsx")])
    assert not und["testable"] and "Dental Chart tab" in und["reason"]
    assert "unknown-screen" in kinds(und)
    assert any("Dental Chart tab" in q and "new screen" in q for q in und["questions"])
    assert [s["found_in_code"] for s in und["screens"]] == [False, True]


def test_unknown_used_screen_only_asks():
    und, _, _ = run(plain_answer(screens=[scr("Allergies widget"), scr("Mystery page", "used")]),
                    lookup=lambda n: [] if "Mystery" in n else [("patient-chart", "x.tsx")])
    assert und["testable"] and "unknown-screen" in kinds(und)
    assert any("which existing screen" in q for q in und["questions"])


def test_no_code_library_skips_the_screen_check():
    und, _, _ = run(lookup=None, catalogue=None)
    assert und["screens"][0]["found_in_code"] is None and und["testable"]
    assert und["meta"]["screen_check"].startswith("skipped")


def test_real_code_library_lookup():
    env = load_env()
    index = u.code_lookup(env)
    if index is None:
        pytest.skip("no code library in SPECBRIDGE_WORKDIR")
    try:
        assert index.find_screen("Allergies widget") and index.find_screen("full Allergies page")
        assert index.find_screen("patient banner") and index.find_screen("login page")
        for fake in ("Dental Chart tab", "Book Flight button", "Crypto wallet", "weather widget"):
            assert index.find_screen(fake) == [], fake
        names = [line for _, line in index.screens_for("Allergies are listed by severity on the Allergies widget")]
        assert len(names) <= 25 and any("allerg" in n for n in names[:5])
    finally:
        index.close()


def test_missing_library_folder_gives_none(tmp_path):
    assert u.code_lookup({"SPECBRIDGE_WORKDIR": str(tmp_path)}) is None
    assert u.code_lookup({}) is None


# --- domain fit and the final decision --------------------------------------------------------------

def test_unrelated_request_goes_to_clarify():
    und, _, _ = run(plain_answer(domain_fit="unrelated", domain_reason="flight booking is not a clinical feature"))
    assert not und["testable"] and "does not fit this product" in und["reason"]
    assert "off-domain" in kinds(und) and any("medical record system" in q for q in und["questions"])


def test_doubtful_request_stays_testable():
    und, _, _ = run(plain_answer(domain_fit="doubtful", domain_reason="a quote of the day is unusual"))
    assert und["testable"] and "off-domain" in kinds(und)


def test_backend_only_is_untestable_even_if_the_ai_says_yes():
    und, _, _ = run(plain_answer(risks=[{"kind": "backend-only", "detail": "database index only"}], testable=True,
                                 screens=[scr("Patient search", "used")]))
    assert not und["testable"] and und["reason"].startswith("backend-only") and und["test_scope"] == "none"


def test_backend_only_change_to_an_existing_screen_gets_a_regression_check():
    und, _, _ = run(plain_answer(risks=[{"kind": "backend-only", "detail": "type refactor"}], testable=False,
                                 screens=[scr("Visit notes workspace", matches="patient-allergy-form-workspace"),
                                          scr("Service queues app", "used")]))
    assert und["testable"] and und["test_scope"] == "regression"
    assert und["regression_screens"] == ["Visit notes workspace"] and "regression check" in und["reason"]


@pytest.mark.parametrize("screen", [scr("Visit notes workspace", status="new"),          # not built yet
                                    scr("Visit notes workspace", "used"),                # only shows server data
                                    scr("Dental Chart tab")])                            # not in the code
def test_backend_only_without_a_real_changed_screen_goes_to_clarify(screen):
    und, _, _ = run(plain_answer(risks=[{"kind": "backend-only", "detail": "x"}], screens=[screen]),
                    lookup=lambda n: [] if "Dental" in n else [("patient-chart", "x.tsx")])
    assert not und["testable"] and und["test_scope"] == "none" and und["regression_screens"] == []


def test_normal_tickets_get_full_scope():
    und, _, _ = run()
    assert und["test_scope"] == "full" and und["regression_screens"] == []


def test_unrelated_beats_backend_only():
    und, _, _ = run(plain_answer(domain_fit="unrelated", risks=[{"kind": "backend-only", "detail": "x"}]))
    assert not und["testable"] and "does not fit" in und["reason"]


def test_no_usable_criteria_is_untestable():
    und, _, _ = run(plain_answer(criteria=[crit("A", status="unclear"), crit("B", status="conflicting")]))
    assert not und["testable"] and "no checkable" in und["reason"]


def test_ticket_asking_to_skip_tests_cannot_make_it_untestable():
    und, _, _ = run(plain_answer(testable=False, reason="the ticket says not to write test cases"),
                    t=ticket(flags=[{"kind": "possible-injection", "detail": "x"}]))
    assert und["testable"] and "was ignored" in und["reason"]


def test_ai_no_is_kept_when_no_rule_applies():
    und, _, _ = run(plain_answer(testable=False, reason="nothing observable", risks=[{"kind": "vague", "detail": "x"}]))
    assert not und["testable"] and und["reason"] == "nothing observable"


def test_decide_order_of_rules():
    a = plain_answer()
    risks = [{"kind": "backend-only", "detail": ""}]
    assert decide(a, [], [], risks, []) == (False, decide(a, [], [], risks, [])[1], "none")
    assert decide(a, [], [], risks, [])[1].startswith("backend-only")


def test_secret_like_text_in_the_answer_is_redacted():
    und, _, _ = run(plain_answer(intent="Log in with password Hunter2025! and key sk-live-abcdefghijklmnop1234"))
    assert "Hunter2025!" not in json.dumps(und) and "sk-live-abcdef" not in json.dumps(und)


def test_finish_never_trusts_ai_ids():
    out = finish(plain_answer(criteria=[{**crit("x"), "id": "AC99"}]), TICKET, FOUND)
    assert out["criteria"][0]["id"] == "AC1"


# --- in the graph -----------------------------------------------------------------------------------

def test_understand_in_the_graph(start):
    r = start("SPEC-66")
    assert [t["node"] for t in r.state["trace"]] == ["START", "intake", "understand", "orchestrator", "criterion_worker", "merge"]
    und = r.state["understanding"]
    assert "injection-attempt" in kinds(und)          # from intake's flag, whatever the AI said
    assert r.state["spent"]["cost"] == pytest.approx(0.0012 + 0.002) and r.state["spent"]["tokens"] == 1200 + 500
    assert json.loads(r.record_path.read_text())["state"]["understanding"]["testable"] is True


def test_ai_failure_in_the_graph_can_be_resumed(start, records):
    broken = fake_understand(brain=FakeBrain(error=BrainError("google returned 503 after 6 tries")))
    with pytest.raises(UnderstandError):
        start("SPEC-1", run_id="busy-1", nodes={"understand": broken})
    assert json.loads((records / "SPEC-1" / "busy-1.json").read_text())["status"] == "error"
    r = start(None, run_id="busy-1", resume=True)
    assert r.status == "complete" and [t["node"] for t in r.state["trace"]] == ["START", "intake", "understand", "orchestrator", "criterion_worker", "merge"]


# --- live: the trick tickets (about $0.005 per ticket at list price; $0 on the free tier) ----------------------------------------

LIVE = pytest.mark.skipif(not (load_env().get("GEMINI_API_KEY") and load_env().get("ATLASSIAN_API_TOKEN")),
                          reason="GEMINI_API_KEY and Jira login needed in .env")
ADVERSARIAL = {t["id"]: t for t in json.loads((PROJECT / "data/golden/adversarial_v0.json").read_text())["tickets"]}
SPEC_OF = json.loads((PROJECT / "data/golden/adversarial_import_map.json").read_text())
OFF_DOMAIN = json.loads((PROJECT / "data/golden/off_domain_v0.json").read_text())["tickets"]


def live_understand(t):
    from specbridge.agent.nodes import intake
    if isinstance(t, str):
        t = intake.node({"ticket_ref": t}, None)["ticket"]
    return u.node({"ticket": t}, None)["understanding"]


@pytest.mark.live
@LIVE
@pytest.mark.parametrize("adv", sorted(ADVERSARIAL))
def test_live_adversarial_ticket(adv):
    expected = ADVERSARIAL[adv]["expected"]
    und = live_understand(SPEC_OF[adv])
    assert und["testable"] is expected["testable"], und["reason"]
    for risk in expected["risks"]:
        assert risk in kinds(und), (risk, und["risks"])
    if adv == "ADV-1":
        assert any("dental" in q.lower() for q in und["questions"])
    if adv == "ADV-4":
        assert [c for c in und["criteria"] if c["status"] == "conflicting"] and und["questions"]
    if adv == "ADV-6":
        assert und["criteria"] and und["questions"]


@pytest.mark.live
@LIVE
@pytest.mark.parametrize("od", OFF_DOMAIN, ids=lambda t: t["id"])
def test_live_domain_fit(od):
    t = {"key": "SPEC-999", "type": od["type"], "title": od["title"], "text": od["text"], "labels": [], "flags": []}
    und = live_understand(t)
    e = od["expected"]
    if "domain_fit" in e:
        assert und["domain_fit"] == e["domain_fit"], und["domain_reason"]
    if "domain_fit_not" in e:
        assert und["domain_fit"] != e["domain_fit_not"], und["domain_reason"]
    assert und["testable"] is e["testable"], und["reason"]
    for risk in e.get("risks", []):
        assert risk in kinds(und)
    for risk in e.get("risks_not", []):
        assert risk not in kinds(und), und["risks"]

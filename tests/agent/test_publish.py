"""Node 11 - publish: the only node that writes outside this machine. Checks first (nothing written if one fails),
then the Confluence page (create, update, or a comment if a person edited it - D10) and one Jira comment."""
import json

import pytest

from specbridge.agent import preflight
from specbridge.agent.limits import Settings
from specbridge.agent.nodes.publish import adf_text, comment_adf, make_node
from specbridge.atlassian import JiraError
from tests.agent.conftest import JIRA_ENV, FakeAtlassian

PAGE = {"title": "UAT SPEC-66: Allergies widget", "labels": ["spec-66", "specbridge", "awaiting-pm-review"],
        "storage": "<h2>1. Summary</h2><p>Sort allergies</p>", "html": "<!doctype html><p>x</p>",
        "markdown": "# x", "comment": "[SpecBridge] SPEC-66: UAT test cases ready for PM review\n6 test cases.\n"
                                      "Page: {page_url}", "summary": {"kind": "test-plan"}}
URL = "https://rooks101.atlassian.net/wiki/spaces/UAT/pages/1001"


def state(**extra):
    return {"run_id": "run-1", "mode": "live", "page": dict(PAGE),
            "ticket": {"key": "SPEC-66", "url": "https://rooks101.atlassian.net/browse/SPEC-66"}, **extra}


def publish(st=None, site=None, env=None, records=None):
    site = site or FakeAtlassian()
    out = make_node(client=site, env=env or JIRA_ENV, records_dir=records)(st or state(), Settings())["published"]
    return out, site


# --- the first run: create ----------------------------------------------------------------------------

def test_first_run_creates_the_page_with_labels_and_property_and_one_jira_comment():
    out, site = publish()
    assert out["error"] == "" and out["page_action"] == "created" and out["page_version"] == 1
    assert out["page_url"] == URL and out["comment_action"] == "created"
    page = site.pages["1001"]
    assert page["storage"] == PAGE["storage"] and page["labels"] == {"spec-66", "specbridge", "awaiting-pm-review"}
    assert page["props"]["specbridge"]["value"] == {"page_version": 1, "run_id": "run-1"}
    [comment] = site.jira_comments["SPEC-66"]
    text = adf_text(comment["body"])
    assert text.startswith("[SpecBridge] SPEC-66") and URL in text and "{page_url}" not in text


def test_the_space_key_confluence_reports_is_used_not_an_old_alias():
    site = FakeAtlassian()
    site.space_key = "SU"                   # the real space: key SU, still found by its old key UAT
    out, site = publish(site=site)
    assert out["page_url"] == "https://rooks101.atlassian.net/wiki/spaces/SU/pages/1001"
    assert site.searched_space == "SU"


def test_the_page_address_in_the_comment_is_a_link():
    adf = comment_adf("[SpecBridge] SPEC-1: x\nPage: {page_url}", URL)
    last = adf["content"][-1]["content"]
    assert last[0] == {"type": "text", "text": "Page: "}
    assert last[1]["marks"] == [{"type": "link", "attrs": {"href": URL}}]


# --- re-runs: update, never overwrite a person's edit --------------------------------------------------

def test_a_rerun_updates_the_same_page_and_the_same_comment():
    _, site = publish()
    st = state(run_id="run-2")
    st["page"]["storage"] = "<p>second draft</p>"
    out, site = publish(st, site)
    assert out["page_action"] == "updated" and out["page_version"] == 2 and out["comment_action"] == "updated"
    assert len(site.pages) == 1 and site.pages["1001"]["storage"] == "<p>second draft</p>"
    assert site.pages["1001"]["version"]["message"] == "[SpecBridge] run run-2"
    assert site.pages["1001"]["props"]["specbridge"]["value"]["page_version"] == 2
    assert len(site.jira_comments["SPEC-66"]) == 1


def test_a_page_edited_by_a_person_is_not_overwritten_the_draft_becomes_a_comment():
    _, site = publish()
    site.edit_by_person("1001")
    out, site = publish(state(run_id="run-2"), site)
    assert out["page_action"] == "draft-as-comment" and out["page_version"] == 2
    assert site.pages["1001"]["storage"] == "<p>edited by the PM</p>"
    assert "update_page" not in site.calls
    [draft] = site.pages["1001"]["comments"]
    assert "edited by a person" in draft and PAGE["storage"] in draft
    assert "added as a comment on the page" in adf_text(site.jira_comments["SPEC-66"][0]["body"])


def test_a_page_with_the_same_title_made_by_a_person_is_not_overwritten():
    site = FakeAtlassian()
    site.create_page("SP1", PAGE["title"], "<p>the PM's own page</p>")
    site.calls.clear()
    out, site = publish(site=site)
    assert out["page_action"] == "draft-as-comment" and site.pages["1001"]["storage"] == "<p>the PM's own page</p>"


def test_a_resume_after_the_page_update_but_before_the_property_is_still_ours():
    _, site = publish()
    page = site.pages["1001"]                      # SpecBridge updated the page, then the run crashed
    page["version"] = {"number": 2, "message": "[SpecBridge] run run-2"}
    out, site = publish(state(run_id="run-2"), site)
    assert out["page_action"] == "updated" and out["page_version"] == 3


def test_someone_elses_specbridge_comment_is_not_touched():
    site = FakeAtlassian()
    site.jira_comments["SPEC-66"] = [{"id": "c-other", "author": {"accountId": "someone-else"},
                                      "body": comment_adf("[SpecBridge] SPEC-66: old", "")}]
    out, site = publish(site=site)
    assert out["comment_action"] == "created" and len(site.jira_comments["SPEC-66"]) == 2
    assert adf_text(site.jira_comments["SPEC-66"][0]["body"]) == "[SpecBridge] SPEC-66: old"


# --- checks before any write ---------------------------------------------------------------------------

@pytest.mark.parametrize("change, message", [
    ({"mode": "dry-run"}, "publish runs only in live mode"),
    ({"ticket": {"key": "OTHER-5"}}, "ticket OTHER-5 is not in project SPEC"),
    ({"ticket": {"key": "SPEC-66", "url": "https://evil.example.com/browse/SPEC-66"}}, "not on the configured"),
    ({"page": None}, "there is no page to publish"),
    ({"page": {**PAGE, "storage": "<p>not closed"}}, "not well-formed XML"),
    ({"page": {**PAGE, "storage": "<p>password: Hunter2025!</p>"}}, "the page contains secret-like text"),
    ({"page": {**PAGE, "comment": "api_key=sk-live-abcdef123456"}}, "the comment contains secret-like text"),
    ({"page": {**PAGE, "storage": "<p>" + "x" * 2_000_001 + "</p>"}}, "at most 2,000,000"),
])
def test_refusals_write_nothing(change, message, records):
    out, site = publish(state(**change), records=records)
    assert out["error"].startswith("not published") and message in out["error"]
    assert site.writes() == [] and out["page_url"] is None


def test_missing_settings_are_refused_without_a_client():
    out = make_node(env={"ATLASSIAN_SITE": "https://rooks101.atlassian.net"})(state(), Settings())["published"]
    assert out["error"].startswith("not published: missing settings in .env")


def test_a_missing_space_is_refused():
    out, site = publish(site=FakeAtlassian(space=False))
    assert "Confluence space UAT was not found" in out["error"] and site.writes() == []


# --- failures: reported, never raised, saved locally ----------------------------------------------------

def test_an_atlassian_error_is_reported_and_the_page_is_saved_locally(records):
    site = FakeAtlassian(errors={"create_page": JiraError("POST /wiki/api/v2/pages -> 403: no permission", 403)})
    out, site = publish(site=site, records=records)
    assert out["error"].startswith("publishing failed: JiraError") and "403" in out["error"]
    files = out["fallback"]["files"]
    assert open(files["storage"], encoding="utf-8").read() == PAGE["storage"]
    assert "/SPEC-66/run-1/" in files["html"].replace("\\", "/")


def test_the_page_is_kept_when_only_the_jira_comment_fails(records):
    site = FakeAtlassian(errors={"add_comment": TimeoutError("timed out")})
    out, site = publish(site=site, records=records)
    assert out["page_action"] == "created" and out["page_url"] == URL
    assert out["comment_id"] is None and out["error"] == "publishing failed: TimeoutError: timed out"
    assert out["fallback"]["files"]


def test_the_token_never_appears_in_the_result():
    site = FakeAtlassian(errors={"find_pages": JiraError("GET search -> 401: Unauthorized", 401)})
    out, _ = publish(site=site)
    assert JIRA_ENV["ATLASSIAN_API_TOKEN"] not in json.dumps(out)


# --- START's check in live mode -------------------------------------------------------------------------

def test_live_mode_needs_the_atlassian_settings():
    with pytest.raises(preflight.PreflightError, match="live mode needs these settings"):
        preflight.check_atlassian(env={"ATLASSIAN_SITE": "x"}, network=False)


def test_live_mode_checks_the_space_online():
    assert preflight.check_atlassian(env=JIRA_ENV, client_factory=lambda e: FakeAtlassian())["network_checked"]
    with pytest.raises(preflight.PreflightError, match="was not found"):
        preflight.check_atlassian(env=JIRA_ENV, client_factory=lambda e: FakeAtlassian(space=False))
    broken = FakeAtlassian(errors={"confluence_space": JiraError("-> 401: Unauthorized", 401)})
    with pytest.raises(preflight.PreflightError, match="cannot read Confluence space UAT"):
        preflight.check_atlassian(env=JIRA_ENV, client_factory=lambda e: broken)


def test_a_failed_atlassian_check_stops_before_any_ai_call(start, records):
    def refuse(env=None, network=True):
        raise preflight.PreflightError("cannot read Confluence space UAT")
    with pytest.raises(preflight.PreflightError):
        start("SPEC-66", mode="live", atlassian_check=refuse)
    assert not list(records.glob("SPEC-66/*.json"))       # no run was created


# --- in the graph ---------------------------------------------------------------------------------------

def test_live_mode_ends_with_publish_not_save_local(start, records):
    site = FakeAtlassian()
    r = start("SPEC-66", mode="live", nodes={"publish": make_node(client=site, env=JIRA_ENV, records_dir=records)})
    nodes = [t["node"] for t in r.state["trace"]]
    assert nodes[-2:] == ["render", "publish"] and "save_local" not in nodes
    assert r.state["published"]["page_action"] == "created" and r.message == ""
    assert site.pages["1001"]["title"] == r.state["page"]["title"]
    rec = json.loads(r.record_path.read_text())
    assert rec["state"]["published"]["page_url"] == URL and rec["mode"] == "live"


def test_a_publish_failure_in_the_graph_keeps_the_run_and_says_so(start, records):
    site = FakeAtlassian(errors={"find_pages": OSError("network down")})
    r = start("SPEC-66", mode="live", nodes={"publish": make_node(client=site, env=JIRA_ENV, records_dir=records)})
    assert "publishing failed: OSError: network down" in r.message
    assert r.state["published"]["fallback"]["files"]


def test_dry_run_never_publishes(start, records):
    site = FakeAtlassian()
    r = start("SPEC-66", nodes={"publish": make_node(client=site, env=JIRA_ENV, records_dir=records)})
    assert site.calls == [] and "published" not in r.state and r.state["saved"]["files"]

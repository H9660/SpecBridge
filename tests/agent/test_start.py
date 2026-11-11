"""Node 0 - START: request checks, settings, brain check, run creation, checkpoints, run record."""
import json
import os
import subprocess
import sys
import urllib.error

import pytest

from specbridge.agent import preflight
from specbridge.agent.graph import StartError
from specbridge.agent.limits import Settings, SettingsError, load_settings
from specbridge.agent.preflight import PreflightError, check_brain
from specbridge.env import load_env
from tests.agent.conftest import FAKE_KEY, PROJECT


def record_of(result):
    return json.loads(result.record_path.read_text(encoding="utf-8"))


def json_files(folder):
    return list(folder.rglob("*.json")) if folder.exists() else []


# --- a normal run ----------------------------------------------------------------------------------

def test_good_run_creates_state_trace_and_record(start, records):
    r = start("  SPEC-1  ")
    s = r.state
    assert r.status == "complete"
    assert s["run_id"] == r.run_id and s["mode"] == "dry-run" and s["ticket_ref"] == "SPEC-1" and s["round"] == 1
    assert isinstance(s["started_at"], float)
    assert [t["node"] for t in s["trace"]] == ["START", "intake", "understand", "orchestrator", "criterion_worker", "merge", "reviewer", "render", "save_local"]
    assert r.record_path == records / "SPEC-1" / f"{r.run_id}.json"
    rec = record_of(r)
    assert rec["status"] == "complete" and rec["error"] is None
    assert rec["brain"]["model"] == "gemini-3.8-flash"
    assert rec["settings"]["cost_cap_usd"] == 0.25 and rec["settings"]["max_rounds"] == 2
    assert len(rec["frozen_commits"]) == 5


def test_eval_mode_is_accepted(start):
    assert start("SPEC-1", mode="eval").state["mode"] == "eval"


@pytest.mark.parametrize("ref, folder", [
    ("https://rooks101.atlassian.net/browse/SPEC-6", "SPEC-6"),
    ("https://rooks101.atlassian.net/jira/software/projects/SPEC/boards/1?selectedIssue=SPEC-16", "SPEC-16"),
    ("spec-55", "SPEC-55"),
])
def test_record_folder_comes_from_the_ticket_key(start, records, ref, folder):
    assert start(ref).record_path.parent == records / folder


def test_a_refused_reference_is_recorded_under_unknown(start, records):
    from specbridge.agent.nodes.intake import IntakeError
    with pytest.raises(IntakeError, match="no ticket key found"):
        start("not a ticket", run_id="unknown-1")
    assert json.loads((records / "unknown" / "unknown-1.json").read_text())["status"] == "error"


def test_record_never_contains_the_api_key(start):
    assert FAKE_KEY not in start().record_path.read_text(encoding="utf-8")


# --- refused before a run exists -------------------------------------------------------------------

@pytest.mark.parametrize("kwargs, message", [
    ({"ticket_ref": ""}, "give a ticket URL or key"),
    ({"ticket_ref": "   \n\t "}, "give a ticket URL or key"),
    ({"ticket_ref": None}, "give a ticket URL or key"),
    ({"ticket_ref": "SPEC-1 " + "x" * 2000}, "at most 2000"),
    ({"mode": "bogus"}, "unknown mode"),
    ({"resume": True}, "--resume needs --run-id"),
    ({"run_id": "../../etc/passwd"}, "a run id may only use"),
    ({"run_id": ""}, "a run id may only use"),
])
def test_refused_requests_create_nothing(start, records, kwargs, message):
    args = {"ticket_ref": "SPEC-1", **kwargs}
    with pytest.raises(StartError, match=message.replace("-", r"\-")):
        start(args.pop("ticket_ref"), **args)
    assert not records.exists()


def test_failed_brain_check_creates_no_record(start, records):
    def no_key(env=None, network=True):
        raise PreflightError("brain 'llm' needs GEMINI_API_KEY in .env")
    with pytest.raises(PreflightError, match="GEMINI_API_KEY"):
        start(brain_check=no_key)
    assert json_files(records) == []


def test_no_preflight_skips_only_the_online_check(start, brain_calls):
    start(preflight_check=False)
    start()
    assert brain_calls == [False, True]


def test_unwritable_records_folder_is_refused(start, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(StartError, match="cannot create"):
        start(records_dir=blocker / "runs")


# --- crashes, Ctrl-C, resume -----------------------------------------------------------------------

def boom(state, settings):
    raise RuntimeError("intake exploded")


def ctrl_c(state, settings):
    raise KeyboardInterrupt


def test_crash_writes_an_error_record_and_reraises(start, records):
    with pytest.raises(RuntimeError, match="intake exploded"):
        start("SPEC-63", run_id="crash-1", nodes={"intake": boom})
    rec = json.loads((records / "SPEC-63" / "crash-1.json").read_text())
    assert rec["status"] == "error" and "intake exploded" in rec["error"]


def test_crashed_run_can_be_resumed(start):
    with pytest.raises(RuntimeError):
        start("SPEC-63", run_id="crash-2", nodes={"intake": boom})
    r = start(None, run_id="crash-2", resume=True)
    assert r.status == "complete"
    assert [t["node"] for t in r.state["trace"]] == ["START", "intake", "understand", "orchestrator", "criterion_worker", "merge", "reviewer", "render", "save_local"]


def test_ctrl_c_writes_interrupted_and_can_resume(start, records):
    with pytest.raises(KeyboardInterrupt):
        start("SPEC-65", run_id="stop-1", nodes={"intake": ctrl_c})
    rec = json.loads((records / "SPEC-65" / "stop-1.json").read_text())
    assert rec["status"] == "interrupted"
    r = start(None, run_id="stop-1", resume=True)
    assert r.status == "complete" and record_of(r)["status"] == "complete"


def test_paused_run_resumes_without_repeating_nodes(start):
    paused = start("SPEC-66", run_id="pause-1", interrupt_before=["intake"])
    assert paused.status == "paused" and record_of(paused)["status"] == "paused"
    assert [t["node"] for t in paused.state["trace"]] == ["START"]
    done = start(None, run_id="pause-1", resume=True)
    assert done.status == "complete"
    assert [t["node"] for t in done.state["trace"]] == ["START", "intake", "understand", "orchestrator", "criterion_worker", "merge", "reviewer", "render", "save_local"]
    assert done.state["started_at"] == paused.state["started_at"]


def test_resume_unknown_run_is_refused(start):
    with pytest.raises(StartError, match="no such run"):
        start(None, run_id="never-ran", resume=True)


def test_resume_finished_run_does_nothing(start):
    first = start("SPEC-6", run_id="done-1")
    again = start(None, run_id="done-1", resume=True)
    assert again.message == "this run already finished" and again.status == "complete"
    assert again.state["trace"] == first.state["trace"]


def test_reusing_a_run_id_is_refused(start):
    start("SPEC-6", run_id="dup-1")
    with pytest.raises(StartError, match="already used"):
        start("SPEC-1", run_id="dup-1")


# --- settings --------------------------------------------------------------------------------------

def write_config(tmp_path, text):
    path = tmp_path / "agent.json"
    path.write_text(text, encoding="utf-8")
    return path


def test_project_config_loads():
    s = load_settings({"BRAIN": "llm"})
    assert (s.cost_cap_usd, s.max_rounds, s.time_cap_seconds, s.max_concurrency) == (0.25, 2, 600, 5)


def test_missing_config_gives_defaults(tmp_path):
    assert load_settings({}, tmp_path / "none.json") == Settings()


def test_concurrency_follows_the_brain(tmp_path):
    path = write_config(tmp_path, '{"max_concurrency": {"llm": 5, "slm": 1}}')
    assert load_settings({"BRAIN": "slm"}, path).max_concurrency == 1
    assert load_settings({}, path).max_concurrency == 5


@pytest.mark.parametrize("text, message", [
    ("{not json", "not valid JSON"),
    ("[1, 2]", "one JSON object"),
    ('{"cost_cap_usd": -1}', "cost_cap_usd must be above 0"),
    ('{"cost_cap_usd": 0}', "cost_cap_usd must be above 0"),
    ('{"max_rounds": 0}', "max_rounds must be at least 1"),
    ('{"max_rounds": "2"}', "max_rounds must be a number"),
    ('{"max_rounds": true}', "max_rounds must be a number"),
    ('{"max_rounds": 1.5}', "max_rounds must be a number"),
    ('{"reserve_share": 1.5}', "at most 0.9"),
    ('{"max_round": 2}', "unknown setting"),
])
def test_broken_config_is_refused(tmp_path, text, message):
    with pytest.raises(SettingsError, match=message):
        load_settings({}, write_config(tmp_path, text))


# --- brain check (preflight) -----------------------------------------------------------------------

MODELS = {"data": [{"id": "models/gemini-3.6-flash"}, {"id": "models/gemini-3.8-flash"}, {"id": "models/gemini-4-argon"}]}


def fake_fetch(answers):
    """answers: url suffix -> JSON reply, or an exception to raise."""
    calls = []

    def fetch(url, headers):
        calls.append((url, headers))
        reply = answers[url.rsplit("/", 1)[1]]
        if isinstance(reply, Exception):
            raise reply
        return reply
    fetch.calls = calls
    return fetch


ENV = {"BRAIN": "llm", "GEMINI_API_KEY": FAKE_KEY}


def test_brain_check_passes_with_one_call():
    fetch = fake_fetch({"models": MODELS})
    info = check_brain(ENV, fetch=fetch)
    assert info["network_checked"] and (info["provider"], info["model"]) == ("google", "gemini-3.6-flash")
    assert [u for u, _ in fetch.calls] == ["https://generativelanguage.googleapis.com/v1beta/openai/models"]
    assert fetch.calls[0][1] == {"Authorization": f"Bearer {FAKE_KEY}"}
    assert "estimates at list price" in info["warnings"][0]


def test_offline_brain_check_makes_no_call():
    fetch = fake_fetch({})
    assert check_brain(ENV, network=False, fetch=fetch)["network_checked"] is False
    assert fetch.calls == []


@pytest.mark.parametrize("env, answers, message", [
    ({"BRAIN": "llm"}, {}, "needs GEMINI_API_KEY"),
    ({"BRAIN": "nope", "GEMINI_API_KEY": FAKE_KEY}, {}, "unknown brain 'nope'"),
    (ENV, {"models": preflight.HTTPStatus(400)}, "google rejected GEMINI_API_KEY"),
    (ENV, {"models": preflight.HTTPStatus(401)}, "google rejected GEMINI_API_KEY"),
    (ENV, {"models": preflight.HTTPStatus(403)}, "google rejected GEMINI_API_KEY"),
    (ENV, {"models": {"data": [{"id": "models/other-model"}]}}, "'gemini-3.6-flash' is not offered"),
    ({**ENV, "BRAIN_MODEL": "gemini-typo"}, {"models": MODELS}, "'gemini-typo' is not offered"),
    (ENV, {"models": urllib.error.URLError("no route")}, "cannot reach google"),
    (ENV, {"models": TimeoutError()}, "cannot reach google"),
    (ENV, {"models": preflight.HTTPStatus(503)}, "answered HTTP 503"),
])
def test_brain_check_refusals_never_show_the_key(env, answers, message):
    with pytest.raises(PreflightError, match=message) as err:
        check_brain(env, fetch=fake_fetch(answers))
    assert FAKE_KEY not in str(err.value)


def test_model_override_is_checked():
    assert check_brain({**ENV, "BRAIN_MODEL": "gemini-4-argon"}, fetch=fake_fetch({"models": MODELS}))["model"] == \
        "gemini-4-argon"


def test_slm_brain_checks_the_local_model():
    fetch = fake_fetch({"models": {"data": [{"id": "llama3:8b"}]}})
    with pytest.raises(PreflightError, match="ollama pull"):
        check_brain({"BRAIN": "slm"}, fetch=fetch)
    assert [u.rsplit("/", 1)[1] for u, _ in fetch.calls] == ["models"]


# --- command line ----------------------------------------------------------------------------------

def cli(*args, key=FAKE_KEY):
    """The command line in a subprocess; key=None keeps the real key from .env."""
    env = {**os.environ, "BRAIN": "llm", **({} if key is None else {"GEMINI_API_KEY": key})}
    return subprocess.run([sys.executable, str(PROJECT / "scripts" / "run_ticket.py"), *args],
                          capture_output=True, text=True, env=env, timeout=60)


@pytest.mark.live
@pytest.mark.skipif(not (load_env().get("ATLASSIAN_API_TOKEN") and load_env().get("GEMINI_API_KEY")),
                    reason="Jira login and GEMINI_API_KEY needed in .env")
def test_cli_runs_a_ticket(records):
    out = cli("SPEC-1", "--records-dir", str(records), key=None)
    assert out.returncode == 0, out.stderr
    assert "status: complete" in out.stdout and "run:" in out.stdout and str(records / "SPEC-1") in out.stdout
    assert FAKE_KEY not in out.stdout + out.stderr


@pytest.mark.parametrize("args, message", [
    (["SPEC-1", "--mode", "bogus"], "unknown mode"),
    (["   "], "give a ticket URL or key"),
    (["--resume"], "--resume needs --run-id"),
])
def test_cli_refusals_exit_2(records, args, message):
    out = cli(*args, "--no-preflight", "--records-dir", str(records))
    assert out.returncode == 2 and message in out.stderr


def test_cli_missing_key_exits_2(records):
    out = cli("SPEC-1", "--no-preflight", "--records-dir", str(records), key="")
    assert out.returncode == 2 and "GEMINI_API_KEY" in out.stderr


# --- live (needs GEMINI_API_KEY in .env) -----------------------------------------------------------

@pytest.mark.live
@pytest.mark.skipif(not load_env().get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set in .env")
def test_live_brain_check():
    info = check_brain()
    assert info["network_checked"] and info["provider"] == "google"

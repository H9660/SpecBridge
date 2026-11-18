"""The SLM host (scripts/slm_host.py) and the SLM brain (specbridge/brain.py SLMHostBrain), ADR D29.

A fake Ollama, the real host server and the real brain run together on 127.0.0.1; no GPU or network needed.
"""
import importlib.util
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from specbridge import brain as brain_mod  # noqa: E402
from specbridge.agent import limits  # noqa: E402
from specbridge.agent.worker import criterion_worker  # noqa: E402
from specbridge.brain import BrainError, SLMHostBrain, load_brain  # noqa: E402

spec = importlib.util.spec_from_file_location("slm_host", PROJECT / "scripts" / "slm_host.py")
slm_host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slm_host)

KEY = "test-key-0123456789abcdef"
MODELS = {"qwen2.5-coder:14b": 32768, "qwen2.5-coder:7b": 20480, "llama3.1:8b": 24576}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["kind"],
          "properties": {"kind": {"type": "string", "enum": ["bug", "story"]}}}


class FakeOllama:
    """/api/chat answers from a script of (status, content or body); after the script, a default JSON answer."""

    def __init__(self):
        self.calls, self.script, self.delay = [], [], 0.0
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, status, body):
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                if self.path == "/api/tags":
                    return self._send(200, {"models": [{"name": m, "model": m} for m in MODELS]})
                return self._send(200, {"version": "fake"})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fake.calls.append(body)
                time.sleep(fake.delay)
                status, content = fake.script.pop(0) if fake.script else (200, '{"kind": "bug"}')
                if status != 200:
                    return self._send(status, {"error": content})
                return self._send(200, {"model": body["model"], "message": {"role": "assistant", "content": content},
                                        "done_reason": "stop", "prompt_eval_count": 40, "eval_count": 7})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


@pytest.fixture
def stack():
    ollama = FakeOllama()
    host = slm_host.Host(ollama.url, MODELS, KEY)
    server = slm_host.make_server(host, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    yield ollama, host, url
    server.shutdown()
    ollama.server.shutdown()


def make_brain(url, role=None, **profile):
    b = load_brain(env={"BRAIN": "slm", "SLM_API_KEY": KEY, "SLM_BASE_URL": url}, role=role)
    b.profile.update({"poll_seconds": 0.02, **profile})
    return b


def http(method, url, body=None, key=KEY):
    headers = {"Content-Type": "application/json", **({"Authorization": f"Bearer {key}"} if key else {})}
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


# --- translation --------------------------------------------------------------------------------------------

def test_request_becomes_ollama_chat_with_context_schema_and_limits():
    req = {"model": "qwen2.5-coder:14b", "max_tokens": 4000, "temperature": 0,
           "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
           "response_format": {"type": "json_schema", "json_schema": {"name": "a", "strict": True, "schema": SCHEMA}}}
    body, note = slm_host.to_ollama(req, 32768)
    assert body["format"] == SCHEMA and body["stream"] is False and body["keep_alive"] == -1
    assert body["options"] == {"num_ctx": 32768, "num_predict": 4000, "temperature": 0.0}
    assert body["messages"] == req["messages"] and note == ""


def test_answer_limit_lowered_when_prompt_is_long_and_refused_when_it_cannot_fit():
    long = {"model": "m", "max_tokens": 8000, "messages": [{"role": "user", "content": "x" * 75_000}]}
    body, note = slm_host.to_ollama(long, 32768)
    assert body["options"]["num_predict"] == 32768 - 25_000 and "limited" in note
    short, _ = slm_host.to_ollama({**long, "max_tokens": 20}, 32768)
    assert short["options"]["num_predict"] == 20                # a small limit is kept, never raised
    tight, _ = slm_host.to_ollama({**long, "messages": [{"role": "user", "content": "x" * 96_000}]}, 32768)
    assert tight["options"]["num_predict"] == slm_host.MIN_ANSWER_TOKENS
    with pytest.raises(slm_host.TooLong):
        slm_host.to_ollama({**long, "messages": [{"role": "user", "content": "x" * 130_000}]}, 32768)
    with pytest.raises(slm_host.BadRequest):
        slm_host.to_ollama({"model": "m", "messages": [{"role": "tool", "content": "x"}]}, 32768)


def test_ollama_answer_in_openai_shape():
    out = slm_host.from_ollama({"message": {"content": "hi"}, "done_reason": "length", "prompt_eval_count": 5,
                                "eval_count": 3}, "m")
    assert out["choices"][0] == {"index": 0, "message": {"role": "assistant", "content": "hi"},
                                 "finish_reason": "length"}
    assert out["usage"] == {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8} and out["model"] == "m"


# --- the host server ----------------------------------------------------------------------------------------

def test_only_health_is_open_everything_else_needs_the_key(stack):
    _, _, url = stack
    assert http("GET", url + "/health", key=None) == (200, {"ok": True})
    assert http("GET", url + "/v1/models", key=None)[0] == 401
    assert http("GET", url + "/v1/models", key="wrong-key-0123456789")[0] == 401
    status, models = http("GET", url + "/v1/models")
    assert status == 200 and [m["id"] for m in models["data"]] == list(MODELS)


def test_same_job_id_runs_once(stack):
    ollama, _, url = stack
    job = {"id": "job-0001-abcd", "request": {"model": "qwen2.5-coder:7b", "messages": [{"role": "user",
                                                                                          "content": "hi"}]}}
    assert http("POST", url + "/v1/jobs", job)[0] == 202
    assert http("POST", url + "/v1/jobs", job)[0] == 200
    for _ in range(100):
        status, state = http("GET", url + "/v1/jobs/job-0001-abcd")
        if state["status"] == "done":
            break
        time.sleep(0.02)
    assert state["status"] == "done" and len(ollama.calls) == 1
    assert http("GET", url + "/v1/jobs/unknown-job-id")[0] == 404


def test_unknown_model_is_refused(stack):
    ollama, _, url = stack
    status, body = http("POST", url + "/v1/chat/completions",
                        {"model": "llama3.3:70b", "messages": [{"role": "user", "content": "hi"}]})
    assert status == 400 and "not served" in body["error"]["message"] and ollama.calls == []


# --- the brain through the host -----------------------------------------------------------------------------

def test_brain_gets_checked_json_through_jobs(stack):
    ollama, _, url = stack
    b = make_brain(url)
    assert isinstance(b, SLMHostBrain)
    r = b.ask_json("Classify: the save button fails", SCHEMA)
    assert r.data == {"kind": "bug"} and r.model == "qwen2.5-coder:14b" and r.provider == "ollama"
    assert (r.input_tokens, r.output_tokens, r.cost_usd) == (40, 7, None)
    sent = ollama.calls[0]
    assert sent["format"] == SCHEMA and sent["options"]["num_ctx"] == 32768


def test_roles_use_their_own_models_and_contexts(stack):
    ollama, _, url = stack
    make_brain(url, role="worker_agent").ask("hi")
    make_brain(url, role="reviewer").ask("hi")
    assert [(c["model"], c["options"]["num_ctx"]) for c in ollama.calls] == [("qwen2.5-coder:7b", 20480),
                                                                              ("llama3.1:8b", 24576)]


def test_invalid_json_is_asked_again_like_any_brain(stack):
    ollama, _, url = stack
    ollama.script = [(200, '{"kind": "epic"}')]
    r = make_brain(url).ask_json("Classify", SCHEMA)
    assert r.data == {"kind": "bug"} and r.attempts == 2 and len(ollama.calls) == 2


def test_busy_ollama_is_retried(stack, monkeypatch):
    monkeypatch.setattr(brain_mod.time, "sleep", lambda s: None)
    ollama, _, url = stack
    ollama.script = [(500, "out of memory, try again")]
    r = make_brain(url, poll_seconds=0.0).ask("hi")
    assert r.text == '{"kind": "bug"}' and len(ollama.calls) == 2


def test_refused_request_is_not_retried(stack):
    ollama, _, url = stack
    with pytest.raises(BrainError, match="413"):
        make_brain(url).ask("x" * 140_000)
    assert ollama.calls == []


def test_lost_job_is_sent_again_and_runs_once(stack):
    ollama, host, url = stack
    real_get, lost = host.get, []

    def forgetful(job_id):
        if not lost:
            lost.append(job_id)
            return None
        return real_get(job_id)
    host.get = forgetful
    r = make_brain(url).ask("hi")
    assert r.text and lost and len(ollama.calls) == 1


def test_wrong_key_gives_a_clear_error(stack):
    _, _, url = stack
    b = make_brain(url)
    b._api_key = "wrong-key-0123456789"
    with pytest.raises(BrainError, match="refused SLM_API_KEY"):
        b.ask("hi")


def test_unreachable_host_fails_after_unreachable_seconds():
    b = make_brain("http://127.0.0.1:9", unreachable_seconds=0.5)
    start = time.time()
    with pytest.raises(BrainError, match="cannot reach the SLM host.*SLM_BASE_URL"):
        b.ask("hi")
    assert time.time() - start < 5


def test_slow_answer_hits_the_call_timeout_and_the_waiting_job_is_cancelled(stack):
    ollama, host, url = stack
    ollama.delay = 1.2
    slow = make_brain(url, timeout_seconds=0.3)
    with pytest.raises(BrainError, match="no answer from the SLM host"):
        slow.ask("first")                       # running: cannot be cancelled, finishes on its own
    with pytest.raises(BrainError, match="no answer from the SLM host"):
        slow.ask("second")                      # waits behind the first: cancelled
    time.sleep(1.6)
    assert sorted(j["status"] for j in host.jobs.values()) == ["cancelled", "done"]


# --- settings -------------------------------------------------------------------------------------------------

def test_load_brain_slm_needs_the_key_and_takes_the_address_with_or_without_v1():
    with pytest.raises(BrainError, match="SLM_API_KEY"):
        load_brain(env={"BRAIN": "slm"})
    for given in ("https://abc.trycloudflare.com", "https://abc.trycloudflare.com/", "https://abc.trycloudflare.com/v1"):
        assert load_brain(env={"BRAIN": "slm", "SLM_API_KEY": KEY, "SLM_BASE_URL": given}).base_url == \
            "https://abc.trycloudflare.com/v1"
    assert load_brain(env={"BRAIN": "slm", "SLM_API_KEY": KEY}).base_url == "http://127.0.0.1:8000/v1"
    with pytest.raises(BrainError, match="http"):
        load_brain(env={"BRAIN": "slm", "SLM_API_KEY": KEY, "SLM_BASE_URL": "abc.trycloudflare.com"})
    llm = load_brain(env={"GEMINI_API_KEY": "k", "SLM_BASE_URL": "https://abc.trycloudflare.com"})
    assert "googleapis" in llm.base_url          # the SLM address never redirects the cloud brain


def test_time_cap_and_concurrency_per_brain(tmp_path):
    cfg = tmp_path / "agent.json"
    cfg.write_text(json.dumps({"time_cap_seconds": {"llm": 600, "slm": 3600}, "max_concurrency": {"llm": 5, "slm": 1}}))
    slm = limits.load_settings(env={"BRAIN": "slm"}, config_path=cfg)
    llm = limits.load_settings(env={}, config_path=cfg)
    assert (slm.time_cap_seconds, slm.max_concurrency) == (3600, 1)
    assert (llm.time_cap_seconds, llm.max_concurrency) == (600, 5)


def test_worker_prompt_sizes_follow_the_brain_profile():
    evidence = [{"id": f"E{i}", "repo": "r", "path": f"p{i}.tsx", "lines": [1, 9], "text": "x" * 5000, "why": ""}
                for i in range(1, 9)]
    item = {"slice": {"criteria": [], "ticket_lines": []}, "criterion_ids": []}
    small = criterion_worker.cases_message({}, item, evidence, evidence_chars=12_000)
    assert small.count("(not shown: space)") == 6
    slm = load_brain(env={"BRAIN": "slm", "SLM_API_KEY": KEY})
    assert criterion_worker._profile_limit(slm, "evidence_chars", 48_000) == 32_000
    assert criterion_worker._profile_limit(object(), "evidence_chars", 48_000) == 48_000

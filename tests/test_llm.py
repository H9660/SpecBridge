"""llm.py with LiteLLM mocked: no network, no API key needed."""
import json
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from specbridge import llm
from specbridge.models import StepTrace


class Answer(BaseModel):
    verdict: str


def fake_response(content, cost=None, tool_calls=None, prompt_tokens=10, completion_tokens=5):
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, cost=cost)
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage, model="fake/model",
                           _hidden_params={})


@pytest.fixture
def calls(monkeypatch):
    log, queue = [], []

    def completion(**kwargs):
        log.append(kwargs)
        return queue.pop(0)

    monkeypatch.setattr(llm.litellm, "completion", completion)
    monkeypatch.setattr(llm.litellm, "completion_cost", lambda **kw: (_ for _ in ()).throw(Exception("no price")))
    return SimpleNamespace(log=log, queue=queue)


MSGS = [{"role": "user", "content": "hi"}]


def test_plain_text_records_usage_and_trace(calls):
    calls.queue.append(fake_response("hello", cost=0.0012))
    r = llm.complete(MSGS, "openrouter/google/gemini-3.8-flash", prompt_hash="p1", env={})
    assert (r.text, r.input_tokens, r.output_tokens, r.cost_usd, r.attempts) == ("hello", 10, 5, 0.0012, 1)
    assert r.latency_ms >= 0 and r.prompt_hash == "p1"
    trace = r.trace("baseline")
    assert isinstance(trace, StepTrace) and trace.model == "fake/model" and trace.cost_usd == 0.0012
    sent = calls.log[0]
    assert sent["temperature"] == 0.0 and sent["extra_body"] == {"usage": {"include": True}}


def test_api_key_comes_from_env_and_is_scrubbed_from_errors(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError(f"bad key {kwargs['api_key']}")

    monkeypatch.setattr(llm.litellm, "completion", boom)
    with pytest.raises(llm.LLMError) as err:
        llm.complete(MSGS, "openrouter/x", env={"OPENROUTER_API_KEY": "sk-or-secret"})
    assert "sk-or-secret" not in str(err.value) and "***" in str(err.value)


def test_json_retry_once_then_valid(calls):
    calls.queue += [fake_response("not json", cost=0.001),
                    fake_response('```json\n{"verdict": "pass"}\n```', cost=0.002)]
    r = llm.complete(MSGS, "openrouter/x", response_model=Answer, env={})
    assert r.data == Answer(verdict="pass") and r.attempts == 2
    assert (r.input_tokens, r.output_tokens, r.cost_usd) == (20, 10, 0.003)
    retry_msgs = calls.log[1]["messages"]
    assert retry_msgs[-1]["role"] == "user" and "did not match the schema" in retry_msgs[-1]["content"]
    assert calls.log[0]["response_format"]["json_schema"]["name"] == "Answer"


def test_json_invalid_twice_raises(calls):
    calls.queue += [fake_response("{}"), fake_response("{}")]
    with pytest.raises(llm.LLMError, match="invalid JSON twice"):
        llm.complete(MSGS, "openrouter/x", response_model=Answer, env={})


def test_unknown_cost_is_none_not_zero(calls):
    calls.queue.append(fake_response("x", cost=None))
    assert llm.complete(MSGS, "ollama_chat/qwen", api_base="http://127.0.0.1:11434", env={}).cost_usd is None
    assert calls.log[0]["api_base"] == "http://127.0.0.1:11434" and "extra_body" not in calls.log[0]


def test_tool_calls_are_captured(calls):
    call = SimpleNamespace(id="c1", function=SimpleNamespace(name="search_code", arguments=json.dumps({"query": "q"})))
    calls.queue.append(fake_response(None, tool_calls=[call]))
    r = llm.complete(MSGS, "openrouter/x", tools=[{"type": "function"}], env={})
    assert r.text == "" and r.tool_calls == [{"id": "c1", "name": "search_code", "arguments": '{"query": "q"}'}]


def test_prompt_hash_is_stable():
    assert llm.text_hash("abc") == llm.text_hash("abc") != llm.text_hash("abd")


def test_runs_on_real_litellm_response_and_zero_price_is_unknown():
    """LiteLLM's mock_response returns a real ModelResponse (no network). Its price table lists our OpenRouter
    models at 0, so without a provider-reported cost the result must be None, never a fake $0."""
    r = llm.complete(MSGS, "openrouter/google/gemini-3.8-flash", env={}, mock_response="hello")
    assert r.text == "hello" and r.input_tokens > 0 and r.output_tokens > 0
    assert r.cost_usd is None and r.tool_calls == []


def test_openrouter_reported_cost_wins():
    resp = fake_response("x", cost=None)
    resp._hidden_params = {"additional_headers": {"llm_provider-x-litellm-response-cost": 0.0042}}
    assert llm.response_cost(resp, "openrouter/google/gemini-3.8-flash") == 0.0042


def test_real_price_table_is_used_when_priced():
    r = llm.complete(MSGS, "gpt-4o", env={}, mock_response="hello")
    assert r.cost_usd is not None and r.cost_usd > 0

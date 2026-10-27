"""The only way SpecBridge talks to a model: a thin LiteLLM wrapper that records tokens, cost and latency.

Every call returns an `LLMResult` that maps straight onto a `StepTrace`. Prompts are files (see `load_prompt`);
their hash goes into the trace. JSON answers are validated against a Pydantic model and retried once with the
validation error appended. API keys are read from .env and passed to LiteLLM, never logged or returned.
"""
import hashlib
import json
import re
import time
from dataclasses import dataclass, field

import litellm
from pydantic import BaseModel, ValidationError

from specbridge.env import PROJECT, load_env
from specbridge.models import StepTrace

litellm.suppress_debug_info = True
litellm.drop_params = True  # e.g. temperature on models that reject it; the trace still records what was asked

KEY_ENV = {"openrouter": "OPENROUTER_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
           "gemini": "GEMINI_API_KEY"}


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResult:
    text: str
    data: BaseModel | None
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    latency_ms: int
    prompt_hash: str
    attempts: int
    tool_calls: list[dict] = field(default_factory=list)

    def trace(self, step, loop=0, notes=""):
        return StepTrace(step=step, loop=loop, prompt_hash=self.prompt_hash, model=self.model,
                         input_tokens=self.input_tokens, output_tokens=self.output_tokens, cost_usd=self.cost_usd,
                         latency_ms=self.latency_ms, tool_calls=self.tool_calls, notes=notes)


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_prompt(relpath):
    """(text, hash) of a prompt file under prompts/. Prompts are never inline strings."""
    text = (PROJECT / "prompts" / relpath).read_text(encoding="utf-8")
    return text, text_hash(text)


def complete(messages, model, *, prompt_hash=None, response_model=None, tools=None, temperature=0.0,
             max_tokens=4000, api_base=None, timeout=180, retries=2, env=None, **extra):
    """One logical model call (up to two requests if a JSON answer fails validation)."""
    env = load_env() if env is None else env
    kwargs = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "timeout": timeout,
              "num_retries": retries, **extra}
    key_env = KEY_ENV.get(model.split("/", 1)[0])
    if key_env and env.get(key_env):
        kwargs["api_key"] = env[key_env]
    if api_base:
        kwargs["api_base"] = api_base
    if model.startswith("openrouter/"):
        kwargs["extra_body"] = {"usage": {"include": True}}  # OpenRouter then reports the real cost
    if tools:
        kwargs["tools"] = tools
    if response_model is not None:
        kwargs["response_format"] = {"type": "json_schema", "json_schema": {
            "name": response_model.__name__, "schema": response_model.model_json_schema()}}
    prompt_hash = prompt_hash or text_hash(json.dumps(messages, sort_keys=True))

    start, attempts, tokens_in, tokens_out, costs = time.monotonic(), 0, 0, 0, []
    while True:
        attempts += 1
        try:
            resp = litellm.completion(messages=messages, **kwargs)
        except Exception as err:  # LiteLLM raises provider-specific types; surface one readable error
            raise LLMError(f"{model} call failed: {type(err).__name__}: {_scrub(str(err), kwargs)[:300]}") from None
        usage = getattr(resp, "usage", None)
        tokens_in += getattr(usage, "prompt_tokens", 0) or 0
        tokens_out += getattr(usage, "completion_tokens", 0) or 0
        costs.append(response_cost(resp, model))
        message = resp.choices[0].message
        text = message.content or ""
        data, problem = (None, None) if response_model is None else _validate(text, response_model)
        if problem is None or attempts == 2:
            break
        messages = messages + [{"role": "assistant", "content": text},
                               {"role": "user", "content": f"That did not match the schema: {problem}\n"
                                                           "Reply again with corrected JSON only."}]
    if problem:
        raise LLMError(f"{model} gave invalid JSON twice: {problem}")
    known = [c for c in costs if c is not None]
    return LLMResult(text=text, data=data, model=getattr(resp, "model", None) or model, input_tokens=tokens_in,
                     output_tokens=tokens_out, cost_usd=round(sum(known), 6) if known else None,
                     latency_ms=int((time.monotonic() - start) * 1000), prompt_hash=prompt_hash,
                     attempts=attempts, tool_calls=_tool_calls(message))


def response_cost(resp, model):
    """Provider-reported cost first, then LiteLLM's price table if it has a real price, else None (unknown).

    Never 0.0 by default: LiteLLM lists some OpenRouter models at price 0, which would make a run look free.
    """
    hidden = getattr(resp, "_hidden_params", None) or {}
    cost = (hidden.get("additional_headers") or {}).get("llm_provider-x-litellm-response-cost")  # OpenRouter
    if cost is None:
        cost = getattr(getattr(resp, "usage", None), "cost", None)
    if cost is None and _priced(model):
        try:
            cost = litellm.completion_cost(completion_response=resp, model=model)
        except Exception:  # price table could not cost this response
            cost = None
    return float(cost) if cost is not None else None


def _priced(model):
    try:
        info = litellm.get_model_info(model)
    except Exception:  # model missing from LiteLLM's price table
        return False
    return bool(info.get("input_cost_per_token") or info.get("output_cost_per_token"))


def _validate(text, response_model):
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    raw = (fenced.group(1) if fenced else text).strip()
    try:
        return response_model.model_validate_json(raw), None
    except ValidationError as err:
        return None, "; ".join(f"{'.'.join(map(str, e['loc'])) or '$'}: {e['msg']}" for e in err.errors()[:5])


def _tool_calls(message):
    calls = getattr(message, "tool_calls", None) or []
    return [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments} for c in calls]


def _scrub(text, kwargs):
    key = kwargs.get("api_key")
    return text.replace(key, "***") if key else text

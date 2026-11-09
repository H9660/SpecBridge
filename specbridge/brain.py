"""The swappable "brain": one interface for cloud LLMs (OpenRouter) and local SLMs (Ollama).

Everything else in SpecBridge calls `load_brain()` and then `ask()` / `ask_json()`; it never talks
to a model provider directly. Which brain is used comes from config/brains.json:
  BRAIN=llm (default) or BRAIN=slm     pick a profile
  BRAIN_MODEL=<model id>               override the profile's model (e.g. any OpenRouter model)
A provider with a different API style gets a new class with the same methods, added to ADAPTERS.
"""
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from specbridge.env import PROJECT, load_env

CONFIG = PROJECT / "config" / "brains.json"
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
MAX_WAIT_SECONDS = 30


class BrainError(RuntimeError):
    pass


@dataclass
class Reply:
    text: str
    data: object
    brain: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    seconds: float
    attempts: int
    byok: bool | None = None  # True when OpenRouter used the team's own provider key (BYOK)
    cost_estimated: bool = False  # True when cost_usd is worked out from list prices (provider sent none)


class OpenAIChatBrain:
    """Any server that speaks the OpenAI chat-completions format: OpenRouter, Ollama, vLLM, OpenAI."""

    def __init__(self, name, profile, api_key=None, http_retries=None):
        self.name, self.profile = name, profile
        self.provider, self.model = profile["provider"], profile["model"]
        self.base_url = profile["base_url"].rstrip("/")
        self._api_key = api_key
        self.http_retries = profile.get("http_retries", 2) if http_retries is None else http_retries

    def __repr__(self):
        return f"<Brain {self.name}: {self.provider} {self.model}>"

    def _post(self, path, body):
        headers = {"Content-Type": "application/json", **self.profile.get("extra_headers", {})}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        req = urllib.request.Request(f"{self.base_url}{path}", data=json.dumps(body).encode(),
                                     headers=headers, method="POST")
        for attempt in range(self.http_retries + 1):
            wait = min(2 ** (attempt + 1), MAX_WAIT_SECONDS)
            try:
                with urllib.request.urlopen(req, timeout=self.profile.get("timeout_seconds", 180)) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as err:
                raw = err.read().decode(errors="ignore")
                detail = _error_detail(raw)
                # a used-up daily quota cannot succeed before it resets: retrying only wastes time
                daily = err.code == 429 and re.search(r"PerDay|per day", raw, re.I)
                if err.code not in RETRY_STATUS or attempt == self.http_retries or daily:
                    raise BrainError(f"{self.provider} returned {err.code} after {attempt + 1} tries: {detail}") from None
                hint = err.headers.get("Retry-After", "")
                if hint.isdigit():  # busy servers (e.g. free-tier keys) say how long to wait
                    wait = min(int(hint), MAX_WAIT_SECONDS)
            except (urllib.error.URLError, TimeoutError) as err:
                if attempt == self.http_retries:
                    raise BrainError(f"cannot reach {self.provider} at {self.base_url}: {err}") from None
            time.sleep(wait)

    def _chat(self, messages, max_tokens, temperature, response_format=None):
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                "temperature": temperature, **self.profile.get("extra_body", {})}
        if response_format:
            body["response_format"] = response_format
        data = self._post("/chat/completions", body)
        try:
            choice = data["choices"][0]
            text = choice["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise BrainError(f"{self.provider} sent an unexpected answer: {str(data)[:300]}") from None
        if not text.strip() and choice.get("finish_reason") == "length":
            # thinking models spend part of max_tokens on hidden reasoning before writing the answer
            raise BrainError(f"{self.model} used all {max_tokens} tokens before answering; raise max_tokens")
        return text, data.get("usage") or {}, data.get("model", self.model)

    def ask(self, prompt, system=None, max_tokens=2000, temperature=0.0):
        """Plain-text answer."""
        return self._run(_messages(prompt, system), max_tokens, temperature, schema=None)

    def ask_json(self, prompt, schema, system=None, max_tokens=4000, temperature=0.0):
        """Answer as JSON matching `schema` (a JSON Schema). Asks once more if the answer is invalid."""
        system = ((system + "\n\n") if system else "") + \
            "Reply with JSON only, matching this JSON Schema:\n" + json.dumps(schema)
        return self._run(_messages(prompt, system), max_tokens, temperature, schema=schema)

    def _run(self, messages, max_tokens, temperature, schema):
        start, usage_total, attempts = time.time(), [], 0
        fmt = None
        if schema is not None and self.profile.get("structured_outputs"):
            fmt = {"type": "json_schema", "json_schema": {"name": "answer", "strict": True, "schema": schema}}
        while True:
            attempts += 1
            text, usage, model = self._chat(messages, max_tokens, temperature, fmt)
            usage_total.append(usage)
            if schema is None:
                data, problem = None, None
            else:
                data, problem = _parse_json(text, schema)
            if problem is None or attempts == 2:
                break
            messages = messages + [{"role": "assistant", "content": text},
                                   {"role": "user", "content": f"That was not valid: {problem}. "
                                                               "Reply again with corrected JSON only."}]
        if problem:
            raise BrainError(f"{self.name} brain gave invalid JSON twice: {problem}")
        costs = [u["cost"] for u in usage_total if u.get("cost") is not None]
        input_tokens = sum(u.get("prompt_tokens", 0) for u in usage_total)
        output_tokens = sum(_output_tokens(u) for u in usage_total)
        cost, estimated = (sum(costs), False) if costs else (self._list_price(input_tokens, output_tokens), True)
        return Reply(text=text, data=data, brain=self.name, provider=self.provider, model=model.removeprefix("models/"),
                     input_tokens=input_tokens, output_tokens=output_tokens,
                     cost_usd=cost, cost_estimated=estimated and cost is not None,
                     seconds=round(time.time() - start, 2), attempts=attempts,
                     byok=any(u.get("is_byok") for u in usage_total) if any("is_byok" in u for u in usage_total) else None)

    def _list_price(self, input_tokens, output_tokens):
        """Cost at the profile's list price (price_usd_per_mtok), for providers that do not report cost."""
        price = self.profile.get("price_usd_per_mtok")
        if not price:
            return None
        return (input_tokens * price["input"] + output_tokens * price["output"]) / 1e6

    def model_available(self):
        """True if the server lists this brain's model (GET /models)."""
        req = urllib.request.Request(f"{self.base_url}/models", headers=(
            {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}))
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                ids = {m["id"].removeprefix("models/") for m in json.load(resp).get("data", [])}
        except (urllib.error.URLError, TimeoutError) as err:
            raise BrainError(f"cannot reach {self.provider} at {self.base_url}: {err}") from None
        return self.model in ids


ADAPTERS = {"openai-chat": OpenAIChatBrain}


def load_brain(name=None, env=None, config_path=CONFIG):
    """Build the brain chosen by `name`, else BRAIN in the environment/.env, else the config default."""
    env = load_env() if env is None else env
    config = json.loads(config_path.read_text(encoding="utf-8"))
    name = name or env.get("BRAIN") or config["default"]
    if name not in config["brains"]:
        raise BrainError(f"unknown brain '{name}'; choose one of {sorted(config['brains'])} (config/brains.json)")
    profile = dict(config["brains"][name])
    if env.get("BRAIN_MODEL"):
        profile["model"] = env["BRAIN_MODEL"]
    adapter = ADAPTERS.get(profile.get("api"))
    if adapter is None:
        raise BrainError(f"brain '{name}' uses unknown api '{profile.get('api')}'; known: {sorted(ADAPTERS)}")
    api_key = None
    if profile.get("api_key_env"):
        api_key = env.get(profile["api_key_env"])
        if not api_key:
            raise BrainError(f"brain '{name}' needs {profile['api_key_env']} in .env")
    return adapter(name, profile, api_key)


def _error_detail(raw):
    """The useful part of an error body: the provider's message (Google's quota message says which limit was hit
    and when it resets, after a long preamble), else the start of the body."""
    try:
        body = json.loads(raw)
        err = (body[0] if isinstance(body, list) else body).get("error", {})
        message = re.sub(r"\s+", " ", str(err.get("message", ""))).strip()
        if message:
            return f"{err.get('status') or err.get('code', '')}: {message}"[:600]
    except (ValueError, AttributeError, IndexError):
        pass
    return re.sub(r"\s+", " ", raw)[:300]


def _output_tokens(usage):
    """Answer tokens including hidden thinking: some providers (Google) leave thinking out of completion_tokens
    but count it in total_tokens; others report it in completion_tokens_details."""
    completion = usage.get("completion_tokens", 0)
    thinking = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
    total = usage.get("total_tokens")
    if total is not None and total > usage.get("prompt_tokens", 0) + completion:
        return total - usage.get("prompt_tokens", 0)
    return max(completion, thinking)


def _messages(prompt, system):
    return ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]


def _parse_json(text, schema):
    """(data, None) if text is JSON matching schema, else (None, problem). Accepts ```json fences."""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    raw = fenced.group(1) if fenced else text
    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError as err:
        return None, f"not JSON ({err})"
    errors = schema_errors(data, schema)
    return (data, None) if not errors else (None, "; ".join(errors[:5]))


TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}


def schema_errors(value, schema, path="$"):
    """Check the JSON Schema parts we use: type, required, properties, additionalProperties, items, enum."""
    want = schema.get("type")
    if want and (not isinstance(value, TYPES[want]) or (want in ("integer", "number") and isinstance(value, bool))):
        return [f"{path} should be {want}"]
    if "enum" in schema and value not in schema["enum"]:
        return [f"{path} should be one of {schema['enum']}"]
    errors = []
    if want == "object":
        props = schema.get("properties", {})
        errors += [f"{path}.{k} is missing" for k in schema.get("required", []) if k not in value]
        if schema.get("additionalProperties") is False:
            errors += [f"{path}.{k} is not allowed" for k in value if k not in props]
        for k, sub in props.items():
            if k in value:
                errors += schema_errors(value[k], sub, f"{path}.{k}")
    if want == "array" and "items" in schema:
        for i, item in enumerate(value):
            errors += schema_errors(item, schema["items"], f"{path}[{i}]")
    return errors

"""The swappable "brain": one interface for cloud LLMs (Gemini) and small models (SLMs on the SLM host).

Everything else in SpecBridge calls `load_brain()` and then `ask()` / `ask_json()`; it never talks
to a model provider directly. Which brain is used comes from config/brains.json:
  BRAIN=llm (default) or BRAIN=slm     pick a profile
  BRAIN_MODEL=<model id>               override the profile's model (e.g. any OpenRouter model)
A provider with a different API style gets a new class with the same methods, added to ADAPTERS.
The SLM brain talks to scripts/slm_host.py (Ollama on a Kaggle GPU behind a key check and a tunnel, ADR D29),
through a pool of any number of such hosts (specbridge/slm_pool.py, ADR D31).
"""
import json
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass

from specbridge import slm_pool
from specbridge.env import PROJECT, is_certificate_error, load_env, network_hint

CONFIG = PROJECT / "config" / "brains.json"
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
MAX_WAIT_SECONDS = 30
TUNNEL_STATUS = {520, 521, 522, 523, 524, 525, 526, 527, 530}   # Cloudflare: the host or its tunnel is not answering


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
    cached_input_tokens: int = 0  # part of input_tokens the provider served from its prompt cache (if it says)
    host: str | None = None       # the SLM host that answered (ADR D31); None for other brains


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
                if attempt == self.http_retries or is_certificate_error(err):   # retrying cannot fix certificates
                    raise BrainError(f"cannot reach {self.provider} at {self.base_url}: {err}; "
                                     f"{network_hint(err)}") from None
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

    def chat(self, messages, schema=None, max_tokens=4000, temperature=0.0):
        """A multi-turn conversation [{role, content}] (system first, if any). With a schema, the answer is JSON
        checked against it, asked once more if invalid (as ask_json)."""
        messages = [dict(m) for m in messages]
        if schema is not None:
            note = "Reply with JSON only, matching this JSON Schema:\n" + json.dumps(schema)
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] = messages[0]["content"] + "\n\n" + note
            else:
                messages.insert(0, {"role": "system", "content": note})
        return self._run(messages, max_tokens, temperature, schema=schema)

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
        cached = sum((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0 for u in usage_total)
        output_tokens = sum(_output_tokens(u) for u in usage_total)
        cost, estimated = (sum(costs), False) if costs else (self._list_price(input_tokens, output_tokens), True)
        return Reply(text=text, data=data, brain=self.name, provider=self.provider, model=model.removeprefix("models/"),
                     input_tokens=input_tokens, output_tokens=output_tokens, cached_input_tokens=cached,
                     cost_usd=cost, cost_estimated=estimated and cost is not None,
                     seconds=round(time.time() - start, 2), attempts=attempts, host=self._answer_host(),
                     byok=any(u.get("is_byok") for u in usage_total) if any("is_byok" in u for u in usage_total) else None)

    def _answer_host(self):
        return None

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
            raise BrainError(f"cannot reach {self.provider} at {self.base_url}: {err}; {network_hint(err)}") from None
        return self.model in ids


class _HostFailed(Exception):
    """A host gave no usable answer within the patience given (network, tunnel or busy-server errors)."""


class _HostBusy(Exception):
    """The host's job queue is full (503 on submit)."""


class _KeyRefused(Exception):
    pass


class SLMHostBrain(OpenAIChatBrain):
    """SLM hosts (scripts/slm_host.py, ADR D29): Ollama behind a key check, reached through a tunnel; any number of
    them, through the process's host pool (specbridge/slm_pool.py, ADR D31).

    A chat answer is a job: submitted to a host the pool picks (answers at once), then asked for every `poll_seconds`
    until it is done, so no request waits long enough for the tunnel to cut it (about 100 s).
    - The job keeps its id while it moves between hosts, so a host that still has it runs it once.
    - Submit fails (no answer, tunnel error): the job goes to the next host at once. Queue full (503): next host.
    - The host stops answering while it has the job: polled for up to `unreachable_seconds`, then marked down and the
      job sent to another host. A job the host lost (it restarted) is sent again under the same id.
    - The job ends in a busy-server error (5xx): retried on another host, at most `http_retries` times, with a new id.
      413 / 400 are not retried: every host has the same models and contexts.
    - Wrong key or a missing model on one host: that host is left out; on every host: a clear error.
    `timeout_seconds` caps one call, waiting for a free host and in a host's queue included; a job still waiting
    then is cancelled."""

    REQUEST_SECONDS = 30

    def __init__(self, name, profile, api_key=None, http_retries=None):
        super().__init__(name, profile, api_key, http_retries)
        self._local = threading.local()

    def _answer_host(self):
        return getattr(self._local, "host", None)

    def pool(self):
        """The process's pool for this brain's hosts (shared with every other SLM brain using the same hosts)."""
        hosts = self.profile.get("hosts") or [("slm-host", self.base_url)]
        return slm_pool.get_pool(hosts, self._api_key, slm_pool.pool_settings(self.profile),
                                 self.profile.get("hosts_env") or self.profile.get("base_url_env") or "base_url")

    def _post(self, path, body):
        if path != "/chat/completions":
            return super()._post(path, body)
        pool, model = self.pool(), body.get("model")
        timeout = self.profile.get("timeout_seconds", 1800)
        deadline = time.time() + timeout
        job = {"id": uuid.uuid4().hex, "request": body}
        avoid, tries, previous, why = set(), 0, None, ""
        self._local.host = None
        while True:
            try:
                host = pool.acquire(model, deadline, self.profile.get("unreachable_seconds", 120), avoid)
            except slm_pool.PoolError as err:
                raise BrainError(self._pool_message(err, pool, timeout)) from None
            if previous is not None and host.name != previous:
                pool.moved(job["id"], previous, host, why)
            try:
                outcome, state = self._run_job(pool, host, job, deadline, timeout)
            finally:
                pool.release(host)
            previous = host.name
            if outcome == "done":
                pool.answered(host)
                self._local.host = host.name
                return state["result"]
            if outcome != "error":                     # the host failed: the same job goes elsewhere
                avoid.add(host.name)
                why = outcome
                continue
            code = state.get("http_status") or 500
            detail = _error_detail(json.dumps(state.get("result") or {}))
            if code == 400 and "not served" in detail:
                pool.misconfigured(host, f"does not serve {model}", model=model)
                avoid.add(host.name)
                why = f"{host.name} does not serve {model}"
                job = {"id": uuid.uuid4().hex, "request": body}
                continue
            if code not in RETRY_STATUS or tries >= self.http_retries or time.time() >= deadline:
                raise BrainError(f"the SLM host returned {code} after {tries + 1} tries: {detail}")
            tries += 1
            pool.failed(host, f"job ended in HTTP {code}")
            avoid.add(host.name)
            why = f"HTTP {code} on {host.name}"
            job = {"id": uuid.uuid4().hex, "request": body}   # the finished job keeps its error under the old id
            time.sleep(min(2 ** tries, MAX_WAIT_SECONDS))

    def _run_job(self, pool, host, job, deadline, timeout):
        """("done" | "error", the job's state), or (why the host failed, None) when the job must go elsewhere."""
        state, failed = self._submit(pool, host, job)
        if failed:
            return failed, None
        while state.get("status") in ("queued", "running"):
            if time.time() >= deadline:
                self._cancel(host, job["id"])
                where = f" {host.name}" if len(pool.hosts) > 1 else ""
                raise BrainError(f"no answer from the SLM host{where} within {timeout} s (the job was still "
                                 f"{state['status']}); the host may be overloaded")
            time.sleep(self.profile.get("poll_seconds", 2))
            try:
                state = self._call(host, "GET", f"/jobs/{job['id']}", patience=self.profile.get("unreachable_seconds", 120))
            except _HostFailed as err:
                pool.down(host, f"stopped answering during a job ({err})")
                return f"{host.name} stopped answering", None
            except _KeyRefused:
                pool.misconfigured(host, "refused the key", key=True)
                return f"{host.name} refused the key", None
            if state is None:              # the host restarted and lost the job: same id again, so it runs once
                state, failed = self._submit(pool, host, job)
                if failed:
                    return failed, None
        pool.ok(host)
        return ("done" if state.get("status") == "done" else "error"), state

    def _submit(self, pool, host, job):
        """(the job's state, None), or (None, why the host failed)."""
        try:
            state = self._call(host, "POST", "/jobs", job, patience=0)
        except _HostBusy:
            pool.busy(host)
            return None, f"{host.name} was full"
        except _HostFailed as err:
            pool.failed(host, str(err))
            return None, f"{host.name} did not answer"
        except _KeyRefused:
            pool.misconfigured(host, "refused the key", key=True)
            return None, f"{host.name} refused the key"
        pool.ok(host)
        return state, None

    def _call(self, host, method, path, body=None, patience=0):
        """One short request to a host: its JSON answer, or None when a job is unknown (GET 404). Network and tunnel
        errors are tried again until `patience` seconds have passed (0: one try), then _HostFailed."""
        give_up = time.time() + patience
        wait, last = 1, ""
        while True:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"}
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(f"{host.url}{path}", data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.REQUEST_SECONDS) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as err:
                detail = _error_detail(err.read().decode(errors="ignore"))
                if err.code == 404 and method == "GET":
                    return None
                if err.code == 401:
                    raise _KeyRefused() from None
                if err.code == 503 and method == "POST" and "too many jobs" in detail:
                    raise _HostBusy() from None
                if err.code not in RETRY_STATUS | TUNNEL_STATUS:
                    raise BrainError(f"the SLM host {host.name} answered {err.code}: {detail}") from None
                last = f"HTTP {err.code}"
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as err:
                last = str(getattr(err, "reason", None) or err) or type(err).__name__
            if time.time() + wait > give_up:
                raise _HostFailed(last)
            time.sleep(wait)
            wait = min(wait * 2, 15)

    def _cancel(self, host, job_id):
        try:
            req = urllib.request.Request(f"{host.url}/jobs/{job_id}", method="DELETE",
                                         headers={"Authorization": f"Bearer {self._api_key}"})
            urllib.request.urlopen(req, timeout=10).close()
        except (urllib.error.URLError, TimeoutError, OSError):
            pass

    def _pool_message(self, err, pool, timeout):
        where = pool.env_name
        if err.kind == "key":
            key = self.profile.get("api_key_env") or "the key"
            return (f"the SLM host refused {key}: it must be the same key the host was started with "
                    f"(scripts/slm_host.py)" + (f" [{pool.summary()}]" if len(pool.hosts) > 1 else ""))
        if err.kind == "model":
            return (f"no SLM host serves {self.model}; add it to scripts/slm_host.py --models and restart the host "
                    f"[{pool.summary()}]")
        if err.kind == "busy":
            return f"no SLM host was free within {timeout} s; the hosts may be overloaded [{pool.summary()}]"
        if len(pool.hosts) == 1:
            h = pool.hosts[0]
            return (f"cannot reach the SLM host at {h.url} ({h.reason}); is the host (Kaggle notebook) running, and "
                    f"is {where} its current address?")
        return (f"cannot reach any of the {len(pool.hosts)} SLM hosts [{pool.summary()}]; are the hosts (Kaggle "
                f"notebooks) running, and does {where} hold their current addresses?")


ADAPTERS = {"openai-chat": OpenAIChatBrain, "slm-host": SLMHostBrain}


def load_brain(name=None, env=None, config_path=CONFIG, role=None):
    """Build the brain chosen by `name`, else BRAIN in the environment/.env, else the config default.
    `role` (e.g. "worker_agent") picks that role's own model and price from the profile's "roles", if set;
    BRAIN_MODEL overrides only the profile's main model."""
    env = load_env() if env is None else env
    config = json.loads(config_path.read_text(encoding="utf-8"))
    name = name or env.get("BRAIN") or config["default"]
    if name not in config["brains"]:
        raise BrainError(f"unknown brain '{name}'; choose one of {sorted(config['brains'])} (config/brains.json)")
    profile = dict(config["brains"][name])
    if env.get("BRAIN_MODEL"):
        profile["model"] = env["BRAIN_MODEL"]
    if profile.get("base_url_env") and env.get(profile["base_url_env"]):
        profile["base_url"] = _api_root(env[profile["base_url_env"]], profile["base_url_env"])
    if profile.get("api") == "slm-host":
        _slm_hosts(profile, env)
    if role and role in profile.get("roles", {}):
        profile.update(profile["roles"][role])
    adapter = ADAPTERS.get(profile.get("api"))
    if adapter is None:
        raise BrainError(f"brain '{name}' uses unknown api '{profile.get('api')}'; known: {sorted(ADAPTERS)}")
    api_key = None
    if profile.get("api_key_env"):
        api_key = env.get(profile["api_key_env"])
        if not api_key:
            raise BrainError(f"brain '{name}' needs {profile['api_key_env']} in .env")
    return adapter(name, profile, api_key)


def _slm_hosts(profile, env):
    """The SLM hosts (ADR D31): the list in `base_urls_env` (SLM_BASE_URLS), else the one address (SLM_BASE_URL or
    base_url). Sets profile["hosts"] = [(name, url)], profile["hosts_env"] and profile["warnings"]."""
    many_env, one_env = profile.get("base_urls_env"), profile.get("base_url_env")
    profile.setdefault("warnings", [])
    if many_env and env.get(many_env):
        try:
            profile["hosts"] = slm_pool.parse_hosts(env[many_env], many_env)
        except ValueError as err:
            raise BrainError(str(err)) from None
        profile["hosts_env"], profile["base_url"] = many_env, profile["hosts"][0][1]
        if one_env and env.get(one_env):
            profile["warnings"].append(f"both {many_env} and {one_env} are set; {many_env} is used")
    else:
        profile["hosts"], profile["hosts_env"] = [("slm-host", profile["base_url"])], one_env or "base_url"


def _api_root(url, name):
    """A server address from .env (e.g. the tunnel address the SLM host prints), with or without /v1."""
    url = url.strip().rstrip("/")
    if not re.match(r"https?://[^/\s]+", url):
        raise BrainError(f"{name} must be an http(s) address, like https://example.trycloudflare.com/v1")
    return url if url.endswith("/v1") else url + "/v1"


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

"""Step 3 smoke test: does the swappable brain (LLM / SLM adapter) work?

Most checks run against a fake model server on this laptop (free, no key). The live checks call
Gemini directly (Google's OpenAI-compatible endpoint) only when GEMINI_API_KEY is in .env (free tier, or well
under one cent). Writes data/smoke_test_step3.md.

Usage:
  py -3.12 scripts/smoke_test_step3.py
"""
import datetime
import json
import pathlib
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from specbridge import brain as brain_mod  # noqa: E402
from specbridge.brain import BrainError, load_brain  # noqa: E402
from specbridge.env import load_env  # noqa: E402

FAKE_KEY = "sk-or-FAKE-0123456789"
TICKET_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["kind", "steps"],
    "properties": {
        "kind": {"type": "string", "enum": ["bug", "feature"]},
        "steps": {"type": "array", "items": {"type": "string"}},
    },
}
TICKET = ("Bug: on the patient registration form, clicking Save with an empty phone number "
          "shows a blank screen instead of an error message.")


class FakeModelServer:
    """Answers like an OpenAI-compatible server, from a queue of scripted replies."""

    def __init__(self):
        self.replies, self.requests = [], []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, status, body):
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                self._send(200, {"data": [{"id": "fake/model"}, {"id": "qwen2.5-coder:3b"}]})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append({"headers": dict(self.headers), "body": body})
                status, content = outer.replies.pop(0)
                if status != 200:
                    return self._send(status, {"error": {"message": content}})
                finish = "length" if content is None else "stop"
                self._send(200, {"model": body["model"],
                                 "choices": [{"message": {"content": content}, "finish_reason": finish}],
                                 "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.0001}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def brain(self, name="llm", **override):
        config = json.loads(brain_mod.CONFIG.read_text(encoding="utf-8"))
        profile = {**config["brains"][name], "base_url": self.url, "model": "fake/model", **override}
        key = FAKE_KEY if profile.get("api_key_env") else None
        return brain_mod.OpenAIChatBrain(name, profile, key, http_retries=1)

    def script(self, *replies):
        self.replies, self.requests = list(replies), []


def main():
    results = []

    def check(name, status, detail=""):
        if isinstance(status, bool):
            status = "PASS" if status else "FAIL"
        results.append((name, status, detail))

    def attempt(name, fn):
        try:
            fn()
        except Exception as err:  # a smoke test reports instead of crashing
            check(name, "FAIL", f"{type(err).__name__}: {str(err)[:200]}")

    config = json.loads(brain_mod.CONFIG.read_text(encoding="utf-8"))
    needed = {"api", "provider", "base_url", "model", "api_key_env", "structured_outputs", "timeout_seconds"}
    gaps = {n: sorted(needed - set(p)) for n, p in config["brains"].items() if needed - set(p)}
    check("Brain settings file is complete (config/brains.json)",
          not gaps and config["default"] in config["brains"], f"brains: {sorted(config['brains'])}; gaps: {gaps or 'none'}")

    env = {"GEMINI_API_KEY": FAKE_KEY}
    default = load_brain(env=env)
    check("Default brain is the cloud LLM: Gemini, called directly at Google",
          (default.name, default.provider) == ("llm", "google"), repr(default))
    slm = load_brain(env={"BRAIN": "slm"})
    check("BRAIN=slm switches to the local SLM with no code change",
          (slm.name, slm.provider, slm._api_key) == ("slm", "ollama", None), repr(slm))
    other = load_brain(env={**env, "BRAIN_MODEL": "gemini-4-argon"})
    check("BRAIN_MODEL swaps in another Gemini model", other.model == "gemini-4-argon", repr(other))
    errors = []
    for bad_env, expect in (({"BRAIN": "nope"}, "unknown brain"), ({}, "needs GEMINI_API_KEY")):
        try:
            load_brain(env=bad_env)
            errors.append(f"{bad_env}: no error")
        except BrainError as err:
            errors += [] if expect in str(err) else [str(err)]
    check("Clear error for an unknown brain or a missing key", not errors, "; ".join(errors) or "both explained")

    fake = FakeModelServer()

    def plain():
        fake.script((200, "Hello from the fake model"))
        r = fake.brain().ask("Say hello", system="Be brief")
        sent = fake.requests[0]
        ok = (r.text == "Hello from the fake model" and r.input_tokens == 10 and r.cost_usd == 0.0001
              and sent["headers"].get("Authorization") == f"Bearer {FAKE_KEY}"
              and sent["body"]["messages"][0]["role"] == "system")
        check("Plain answer: text, tokens and cost come back", ok, f"{r.text!r}, {r.input_tokens} in, ${r.cost_usd}")
    attempt("Plain answer: text, tokens and cost come back", plain)

    def json_ok():
        fake.script((200, '```json\n{"kind": "bug", "steps": ["Open form", "Click Save"]}\n```'))
        r = fake.brain().ask_json(TICKET, TICKET_SCHEMA)
        fmt = fake.requests[0]["body"].get("response_format", {})
        check("JSON answer checked against the expected shape", r.data["kind"] == "bug" and r.attempts == 1
              and fmt.get("type") == "json_schema", f"data={r.data}")
    attempt("JSON answer checked against the expected shape", json_ok)

    def json_retry():
        fake.script((200, '{"kind": "maybe"}'), (200, '{"kind": "feature", "steps": []}'))
        r = fake.brain().ask_json(TICKET, TICKET_SCHEMA)
        fixup = fake.requests[1]["body"]["messages"][-1]["content"]
        fake.script((200, "not json"), (200, "still not json"))
        try:
            fake.brain().ask_json(TICKET, TICKET_SCHEMA)
            gave_up = "no error"
        except BrainError as err:
            gave_up = "invalid JSON twice" if "invalid JSON twice" in str(err) else str(err)
        check("Bad JSON: asks once more with the problem, then gives a clear error",
              r.attempts == 2 and r.data["kind"] == "feature" and "should be one of" in fixup
              and gave_up == "invalid JSON twice", f"retry fixed it in {r.attempts} tries; second case: {gave_up}")
    attempt("Bad JSON: asks once more with the problem, then gives a clear error", json_retry)

    def http_errors():
        fake.script((503, "busy"), (200, "ok after retry"))
        r = fake.brain().ask("hi")
        fake.script((401, "invalid key"))
        try:
            fake.brain().ask("hi")
            msg = "no error"
        except BrainError as err:
            msg = str(err)
        check("Server busy is retried; wrong key gives a clear error without showing the key",
              r.text == "ok after retry" and "401" in msg and FAKE_KEY not in msg and FAKE_KEY not in repr(fake.brain()),
              msg[:120])
    attempt("Server busy is retried; wrong key gives a clear error without showing the key", http_errors)

    def out_of_tokens():
        fake.script((200, None))
        try:
            fake.brain().ask("hi", max_tokens=20)
            msg = "no error (empty answer returned silently)"
        except BrainError as err:
            msg = str(err)
        check("Model that runs out of tokens while thinking gives a clear error, not an empty answer",
              "raise max_tokens" in msg, msg[:120])
    attempt("Model that runs out of tokens while thinking gives a clear error, not an empty answer", out_of_tokens)

    def slm_path():
        fake.script((200, '{"kind": "bug", "steps": ["a"]}'))
        r = fake.brain("slm", model="qwen2.5-coder:3b").ask_json(TICKET, TICKET_SCHEMA)
        check("Same code path works for a local SLM-style server (no key sent)",
              r.brain == "slm" and "Authorization" not in fake.requests[0]["headers"], f"{r.provider} {r.model}")
    attempt("Same code path works for a local SLM-style server (no key sent)", slm_path)

    tracked = subprocess.run(["git", "grep", "--untracked", "-l", "-E", "sk-or-v1-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}"], cwd=PROJECT,
                             capture_output=True, text=True).stdout.split()
    check("No real API keys in files git could commit (.env excluded by .gitignore)", not tracked,
          ", ".join(tracked) or "none found")

    real_env = load_env()
    live = None
    try:
        if not real_env.get("GEMINI_API_KEY"):
            check("Configured model exists at Google", "PENDING", "add GEMINI_API_KEY to .env (Google lists models only with a key)")
        else:
            live = load_brain("llm", env=real_env)
            check("Configured model exists at Google", live.model_available(), live.model)
    except BrainError as err:
        check("Configured model exists at Google", "FAIL", str(err)[:200])

    names = ("Live LLM: plain answer", "Live LLM: JSON answer about a sample ticket")
    if not real_env.get("GEMINI_API_KEY"):
        for n in names:
            check(n, "PENDING", "add GEMINI_API_KEY to .env")
    else:
        def live_calls():
            b = load_brain("llm", env=real_env)
            r = b.ask("Reply with exactly the word: ready", max_tokens=300)
            check(names[0], "ready" in r.text.lower(), f"{r.model}: {r.text.strip()!r}, ${r.cost_usd}, {r.seconds}s")
            r = b.ask_json(f"Classify this ticket and list 2-4 short test steps.\n\n{TICKET}", TICKET_SCHEMA,
                           max_tokens=400)
            check(names[1], r.data["kind"] == "bug" and 2 <= len(r.data["steps"]) <= 6,
                  f"{r.data['kind']}, {len(r.data['steps'])} steps, {r.attempts} tries, ${r.cost_usd}, {r.seconds}s")
        attempt(names[0], live_calls)
    check("Live SLM (Ollama)", "SKIPPED", "not used yet - SLM model to be chosen later")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Step 3 smoke test - {stamp}", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
    lines += [f"| {i} | {n} | {r} | {d} |" for i, (n, r, d) in enumerate(results, 1)]
    (PROJECT / "data" / "smoke_test_step3.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    raise SystemExit(1 if any(r == "FAIL" for _, r, _ in results) else 0)


if __name__ == "__main__":
    main()

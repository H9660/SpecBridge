#!/usr/bin/env python3
"""SpecBridge SLM host: runs the small models on a GPU machine (Kaggle) and serves them to SpecBridge (ADR D29).

What it starts, in order:
  1. Ollama (installed if missing), with the models pulled, loaded once and checked for a JSON answer
  2. a small server on 127.0.0.1:8000 in front of Ollama that checks a secret key (the only thing exposed)
  3. a Cloudflare quick tunnel to that server, then prints the two lines for the laptop's .env
It then watches Ollama and the tunnel and restarts either one if it stops (a new tunnel prints a new address).

One file, standard library only, Python 3.10+, so it can be copied into a Kaggle notebook as it is.
  Kaggle:  python slm_host.py                              key from SLM_API_KEY or Kaggle Secrets, else made up
  Laptop:  python slm_host.py --no-install --no-tunnel     in front of the Ollama on this machine

Why jobs: Cloudflare ends a request that gets no answer within about 100 s (error 524), and a long answer from a
small model on a T4 takes minutes. So SpecBridge submits a job (POST /v1/jobs answers at once) and asks for it every
few seconds (GET /v1/jobs/<id>). Every request is short, a dropped connection costs only a retry, and the same job
id sent twice runs once. Jobs run one at a time, in order (the agent runs one worker at a time on the SLM anyway).

Endpoints (all but /health need "Authorization: Bearer <key>"):
  GET  /health                  {"ok": true}
  GET  /v1/models               the served models Ollama has, OpenAI style (used by SpecBridge's preflight)
  POST /v1/jobs                 {"id", "request": <OpenAI chat request>} -> the job's state
  GET  /v1/jobs/<id>            {"id", "status": queued|running|done|error|cancelled, "http_status", "result"}
  DELETE /v1/jobs/<id>          cancels a job that has not started
  POST /v1/chat/completions     the same answer without a job (for a quick manual test; may hit the 100 s limit)
"""
import argparse
import hmac
import json
import os
import queue
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

# model=context tokens. Main writer, worker search turns, reviewer (another model family). See ADR D29.
DEFAULT_MODELS = "qwen2.5-coder:14b=32768,qwen2.5-coder:7b=20480,llama3.1:8b=24576"
OLLAMA_URL = "http://127.0.0.1:11434"
PORT = 8000
MAX_BODY = 8 * 1024 * 1024
JOB_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
KEEP_FINISHED_SECONDS = 2 * 3600
MAX_JOBS = 2000
MIN_ANSWER_TOKENS = 1024       # room always left for the answer
CHARS_PER_TOKEN_LOW = 3        # code and JSON: about 3 characters per token at worst (used to leave room)
CHARS_PER_TOKEN_HIGH = 4       # English: about 4 (a prompt is refused only if it is too long even at this rate)
OLLAMA_TIMEOUT = 1800
CLOUDFLARED = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def log(*parts):
    print(time.strftime("%H:%M:%S"), *parts, flush=True)


class BadRequest(ValueError):
    pass


class TooLong(ValueError):
    pass


def parse_models(text):
    """'name=ctx,name=ctx' -> {name: ctx} (in order)."""
    models = {}
    for part in filter(None, (p.strip() for p in text.split(","))):
        name, _, ctx = part.partition("=")
        models[name.strip()] = int(ctx) if ctx.strip() else 32768
    if not models:
        raise SystemExit("no models given")
    return models


def error(message):
    return {"error": {"message": message}}


# --- OpenAI chat request <-> Ollama /api/chat ----------------------------------------------------------------

def to_ollama(req, num_ctx):
    """(Ollama /api/chat body, note). The context size is set on every request, so it never depends on Ollama's
    default; the answer limit is lowered if the prompt would leave it too little room."""
    messages = req.get("messages")
    if not isinstance(messages, list) or not messages:
        raise BadRequest("messages must be a non-empty list")
    out = []
    for m in messages:
        if not isinstance(m, dict) or m.get("role") not in ("system", "user", "assistant") \
                or not isinstance(m.get("content"), str):
            raise BadRequest("each message needs a role (system, user or assistant) and text content")
        out.append({"role": m["role"], "content": m["content"]})
    try:
        wanted = int(req.get("max_tokens") or 2048)
        temperature = float(req.get("temperature", 0.0))
    except (TypeError, ValueError):
        raise BadRequest("max_tokens and temperature must be numbers") from None
    if wanted < 1:
        raise BadRequest("max_tokens must be at least 1")
    fmt = None
    rf = req.get("response_format") or {}
    if rf.get("type") == "json_schema":
        fmt = (rf.get("json_schema") or {}).get("schema")
        if not isinstance(fmt, dict):
            raise BadRequest("response_format.json_schema.schema must be a JSON Schema object")
    elif rf.get("type") == "json_object":
        fmt = "json"
    chars = sum(len(m["content"]) for m in out)
    if chars / CHARS_PER_TOKEN_HIGH > num_ctx - MIN_ANSWER_TOKENS:
        raise TooLong(f"the prompt (about {chars // CHARS_PER_TOKEN_HIGH}+ tokens) does not fit the "
                      f"{num_ctx}-token context of {req.get('model')}")
    num_predict = min(wanted, max(MIN_ANSWER_TOKENS, num_ctx - chars // CHARS_PER_TOKEN_LOW))   # never above wanted
    note = (f"answer limited to {num_predict} tokens (asked {wanted}) to fit the {num_ctx}-token context"
            if num_predict < wanted else "")
    body = {"model": req.get("model"), "messages": out, "stream": False, "keep_alive": -1,
            "options": {"num_ctx": num_ctx, "num_predict": num_predict, "temperature": temperature}}
    if fmt is not None:
        body["format"] = fmt
    return body, note


def from_ollama(resp, model):
    """Ollama's answer in the OpenAI chat-completions shape that specbridge/brain.py reads."""
    content = (resp.get("message") or {}).get("content") or ""
    prompt, answer = int(resp.get("prompt_eval_count") or 0), int(resp.get("eval_count") or 0)
    return {"object": "chat.completion", "model": resp.get("model") or model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                         "finish_reason": "length" if resp.get("done_reason") == "length" else "stop"}],
            "usage": {"prompt_tokens": prompt, "completion_tokens": answer, "total_tokens": prompt + answer}}


# --- the host: jobs in front of Ollama -----------------------------------------------------------------------

class Host:
    def __init__(self, ollama_url, models, key, workers=1, ollama_timeout=OLLAMA_TIMEOUT):
        if len(key) < 16:
            raise SystemExit("the key must be at least 16 characters")
        self.ollama_url, self.models, self.ollama_timeout = ollama_url.rstrip("/"), dict(models), ollama_timeout
        self._auth = f"Bearer {key}".encode()
        self.jobs, self.lock, self.queue = {}, threading.Lock(), queue.Queue()
        self.counts = {"done": 0, "error": 0}
        for _ in range(workers):
            threading.Thread(target=self._work, daemon=True).start()

    def authorized(self, header):
        return hmac.compare_digest((header or "").encode(), self._auth)

    def ollama(self, method, path, body=None, timeout=30):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.ollama_url + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)

    def served_models(self):
        tags = self.ollama("GET", "/api/tags").get("models", [])
        have = {m.get("name") for m in tags} | {m.get("model") for m in tags}
        return {"object": "list", "data": [{"id": m, "object": "model", "owned_by": "ollama", "context": ctx}
                                           for m, ctx in self.models.items() if m in have]}

    def run_chat(self, req):
        """(HTTP status, body). Never raises."""
        model = req.get("model") if isinstance(req, dict) else None
        if model not in self.models:
            return 400, error(f"model {model!r} is not served here; served: {sorted(self.models)}")
        try:
            body, note = to_ollama(req, self.models[model])
        except BadRequest as err:
            return 400, error(str(err))
        except TooLong as err:
            return 413, error(str(err))
        try:
            resp = self.ollama("POST", "/api/chat", body, timeout=self.ollama_timeout)
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="ignore")[:500]
            return (503 if err.code >= 500 else err.code), error(f"Ollama answered {err.code}: {detail}")
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            return 503, error(f"Ollama is not answering: {err}")
        except ValueError as err:
            return 502, error(f"Ollama sent something that is not JSON: {err}")
        out = from_ollama(resp, model)
        if note:
            out["note"] = note
        return 200, out

    @staticmethod
    def public(job):
        return {k: job[k] for k in ("id", "status", "model", "http_status", "result", "created", "started",
                                    "finished") if k in job}

    def submit(self, job_id, req):
        if not isinstance(job_id, str) or not JOB_ID.match(job_id):
            return 400, error("id must be 8-64 letters, digits, '-' or '_'")
        if not isinstance(req, dict):
            return 400, error("request must be an OpenAI chat request object")
        with self.lock:
            self._purge()
            if job_id in self.jobs:                  # the same job sent again (e.g. the answer to the first was lost)
                return 200, self.public(self.jobs[job_id])
            if len(self.jobs) >= MAX_JOBS:
                return 503, error("too many jobs waiting; try again later")
            job = {"id": job_id, "status": "queued", "model": req.get("model"), "created": time.time(),
                   "request": req}
            self.jobs[job_id] = job
            self.queue.put(job_id)
            return 202, self.public(job)

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            return self.public(job) if job else None

    def cancel(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job["status"] == "queued":
                job.update(status="cancelled", finished=time.time())
                job.pop("request", None)
            return self.public(job) if job else None

    def _purge(self):
        old = time.time() - KEEP_FINISHED_SECONDS
        for jid in [j for j, job in self.jobs.items() if job.get("finished", time.time()) < old]:
            del self.jobs[jid]

    def _work(self):
        while True:
            jid = self.queue.get()
            with self.lock:
                job = self.jobs.get(jid)
                if not job or job["status"] != "queued":
                    continue
                job.update(status="running", started=time.time())
                req = job.pop("request")
            try:
                status, body = self.run_chat(req)
            except Exception as err:                 # a bug here must not stop the worker thread
                status, body = 500, error(f"host error: {type(err).__name__}: {err}")
            with self.lock:
                job.update(status="done" if status == 200 else "error", http_status=status, result=body,
                           finished=time.time())
                self.counts["done" if status == 200 else "error"] += 1
            took = job["finished"] - job["started"]
            waited = job["started"] - job["created"]
            log(f"job {jid[:8]} {job['model']}: {job['status']} {status} in {took:.1f}s (waited {waited:.1f}s)"
                + ("" if status == 200 else f" - {body['error']['message'][:200]}"))


class Handler(BaseHTTPRequestHandler):
    server_version = "SpecBridgeSLMHost/1"

    def log_message(self, fmt, *args):          # jobs are logged by the host; skip one line per poll
        pass

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _path(self):
        return urlsplit(self.path).path.rstrip("/")

    def _allowed(self):
        if self.server.host.authorized(self.headers.get("Authorization")):
            return True
        self._send(401, error("missing or wrong key (Authorization: Bearer <SLM_API_KEY>)"))
        return False

    def _json_body(self):
        """(True, the JSON body) or (False, None) after answering with the problem."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self._send(413, error(f"request body must be at most {MAX_BODY} bytes"))
            return False, None
        try:
            return True, json.loads(self.rfile.read(length) or b"null")
        except ValueError:
            self._send(400, error("request body is not JSON"))
            return False, None

    def do_GET(self):
        path, host = self._path(), self.server.host
        if path == "/health":
            return self._send(200, {"ok": True})
        if not self._allowed():
            return None
        if path == "/v1/models":
            try:
                return self._send(200, host.served_models())
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as err:
                return self._send(503, error(f"Ollama is not answering: {err}"))
        if path.startswith("/v1/jobs/"):
            job = host.get(path.rsplit("/", 1)[1])
            return self._send(200, job) if job else self._send(404, error("no such job"))
        return self._send(404, error("not found"))

    def do_POST(self):
        path, host = self._path(), self.server.host
        if not self._allowed():
            return None
        if path not in ("/v1/jobs", "/v1/chat/completions"):
            return self._send(404, error("not found"))
        ok, body = self._json_body()
        if not ok:
            return None
        if path == "/v1/jobs":
            body = body if isinstance(body, dict) else {}
            return self._send(*host.submit(body.get("id"), body.get("request")))
        return self._send(*host.run_chat(body))

    def do_DELETE(self):
        path, host = self._path(), self.server.host
        if not self._allowed():
            return None
        if path.startswith("/v1/jobs/"):
            job = host.cancel(path.rsplit("/", 1)[1])
            return self._send(200, job) if job else self._send(404, error("no such job"))
        return self._send(404, error("not found"))


def make_server(host, port=PORT, bind="127.0.0.1"):
    server = ThreadingHTTPServer((bind, port), Handler)
    server.daemon_threads = True
    server.host = host
    return server


# --- setting up the machine (Kaggle) -------------------------------------------------------------------------

def run(cmd, **kw):
    log("$", cmd if isinstance(cmd, str) else " ".join(cmd))
    return subprocess.run(cmd, **kw)


def install_ollama():
    if shutil.which("ollama"):
        return
    if shutil.which("apt-get"):                  # the install script needs zstd (and lspci to find the GPU)
        run("apt-get update -qq && apt-get install -y -qq zstd pciutils lshw > /dev/null", shell=True)
    run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
    if not shutil.which("ollama"):
        raise SystemExit("Ollama did not install; see the messages above")


def ollama_up(url):
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/version", timeout=5) as resp:
            return json.load(resp).get("version") or "?"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def start_ollama(url, models, log_dir):
    """Popen of `ollama serve`, once it answers."""
    env = {**os.environ, "OLLAMA_HOST": urlsplit(url).netloc, "OLLAMA_KEEP_ALIVE": "-1",
           "OLLAMA_MAX_LOADED_MODELS": str(len(models)), "OLLAMA_NUM_PARALLEL": "1",
           "OLLAMA_CONTEXT_LENGTH": str(max(models.values()))}
    out = open(log_dir / "ollama.log", "ab")
    proc = subprocess.Popen(["ollama", "serve"], env=env, stdout=out, stderr=subprocess.STDOUT)
    for _ in range(120):
        version = ollama_up(url)
        if version:
            log(f"Ollama {version} is running (log: {log_dir / 'ollama.log'})")
            return proc
        if proc.poll() is not None:
            break
        time.sleep(1)
    raise SystemExit(f"Ollama did not start; see {log_dir / 'ollama.log'}")


def pull(url, model):
    env = {**os.environ, "OLLAMA_HOST": urlsplit(url).netloc}
    for attempt in range(1, 4):
        if run(["ollama", "pull", model], env=env).returncode == 0:
            return
        log(f"pull of {model} failed (try {attempt} of 3)")
        time.sleep(5 * attempt)
    raise SystemExit(f"could not pull {model}")


def warm_up(host, model):
    """Loads the model and checks it gives JSON that matches a schema (structured output works)."""
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
    start = time.time()
    status, body = host.run_chat({"model": model, "max_tokens": 50, "temperature": 0,
                                  "messages": [{"role": "user", "content": 'Reply with {"ok": true}'}],
                                  "response_format": {"type": "json_schema", "json_schema": {"schema": schema}}})
    if status != 200:
        raise SystemExit(f"{model} failed its first answer: {body['error']['message']}")
    text = body["choices"][0]["message"]["content"]
    try:
        json.loads(text)
    except ValueError:
        raise SystemExit(f"{model} did not answer in JSON: {text[:200]!r}") from None
    log(f"{model}: loaded and answering JSON ({time.time() - start:.1f}s)")


def gpu_summary():
    if sys.platform == "darwin":
        return "macOS: Ollama uses the Apple GPU (fine for a local test; real runs use the Kaggle T4s)"
    if not shutil.which("nvidia-smi"):
        return "no NVIDIA GPU found: the models will run on the processor, far too slowly. Turn on 'GPU T4 x2'."
    out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip()
    return "GPU: " + "; ".join(out.splitlines())


def cloudflared_binary(cache):
    found = shutil.which("cloudflared")
    if found:
        return found
    path = cache / "cloudflared"
    if not path.exists():
        log("downloading cloudflared")
        urllib.request.urlretrieve(CLOUDFLARED, path)
        path.chmod(0o755)
    return str(path)


class Tunnel:
    """A Cloudflare quick tunnel (no account) to the local server. http2, because some containers block QUIC."""

    def __init__(self, binary, port, log_dir):
        self.binary, self.port, self.log_dir = binary, port, log_dir
        self.proc, self.url = None, None

    def start(self):
        self.url, found = None, threading.Event()
        self.proc = subprocess.Popen([self.binary, "tunnel", "--no-autoupdate", "--protocol", "http2",
                                      "--url", f"http://127.0.0.1:{self.port}"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

        def read(proc=self.proc):
            with open(self.log_dir / "cloudflared.log", "a") as out:
                for line in proc.stderr:
                    out.write(line)
                    out.flush()
                    m = TUNNEL_URL.search(line)
                    if m and not found.is_set():
                        self.url = m.group(0)
                        found.set()
        threading.Thread(target=read, daemon=True).start()
        if not found.wait(90):
            raise SystemExit(f"the tunnel gave no address; see {self.log_dir / 'cloudflared.log'}")
        for _ in range(60):                          # the new name takes a few seconds to work everywhere
            try:
                with urllib.request.urlopen(self.url + "/health", timeout=10) as resp:
                    if json.load(resp).get("ok"):
                        return self.url
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                pass
            time.sleep(2)
        log("warning: the tunnel address does not answer yet; it usually starts working within a minute")
        return self.url

    def alive(self):
        return self.proc is not None and self.proc.poll() is None


def get_key(given):
    if given:
        return given, "given"
    if os.environ.get("SLM_API_KEY"):
        return os.environ["SLM_API_KEY"], "SLM_API_KEY"
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret("SLM_API_KEY"), "Kaggle Secrets"
    except Exception:
        return secrets.token_urlsafe(32), "made up"


def banner(url, key, source):
    line = "=" * 78
    print(f"\n{line}\nSLM host is ready. Put these two lines in SpecBridge's .env (BRAIN=slm):\n", flush=True)
    print(f"SLM_BASE_URL={url}/v1")
    print(f"SLM_API_KEY={key if source == 'made up' else '<the key you stored as SLM_API_KEY (' + source + ')>'}")
    print("\nThen check it from the laptop:  .venv/bin/python scripts/run_ticket.py SPEC-1 --mode dry-run\n"
          "Keep this cell running. If the tunnel restarts, a new address is printed here.\n" + line, flush=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--models", default=DEFAULT_MODELS, help=f"name=context,... (default {DEFAULT_MODELS})")
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--ollama-url", default=OLLAMA_URL)
    p.add_argument("--key", help="the shared secret (default: SLM_API_KEY, then Kaggle Secrets, then made up)")
    p.add_argument("--no-install", action="store_true", help="do not install Ollama")
    p.add_argument("--no-pull", action="store_true", help="do not pull the models")
    p.add_argument("--no-tunnel", action="store_true", help="serve on 127.0.0.1 only (laptop use)")
    p.add_argument("--work-dir", default=str(Path.home() / ".cache" / "specbridge-slm"))
    a = p.parse_args(argv)

    models, work = parse_models(a.models), Path(a.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    key, source = get_key(a.key)
    log(gpu_summary())
    if not a.no_install:
        install_ollama()
    ollama_proc = None if ollama_up(a.ollama_url) else start_ollama(a.ollama_url, models, work)
    if not a.no_pull:
        for m in models:
            pull(a.ollama_url, m)
    host = Host(a.ollama_url, models, key)
    for m in models:
        warm_up(host, m)
    server = make_server(host, a.port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log(f"key-checking server on http://127.0.0.1:{a.port} (key: {source}); models: {models}")

    tunnel = None
    if a.no_tunnel:
        banner(f"http://127.0.0.1:{a.port}", key, source)
    else:
        tunnel = Tunnel(cloudflared_binary(work), a.port, work)
        banner(tunnel.start(), key, source)

    last_beat = time.time()
    try:
        while True:
            time.sleep(15)
            if ollama_proc is not None and ollama_proc.poll() is not None:
                log("Ollama stopped; starting it again")
                ollama_proc = start_ollama(a.ollama_url, models, work)
            if tunnel is not None and not tunnel.alive():
                log("the tunnel stopped; starting a new one (new address below)")
                banner(tunnel.start(), key, source)
            if time.time() - last_beat > 600:
                with host.lock:
                    waiting = sum(1 for j in host.jobs.values() if j["status"] in ("queued", "running"))
                log(f"alive: {host.counts['done']} answers, {host.counts['error']} errors, {waiting} waiting")
                last_beat = time.time()
    except KeyboardInterrupt:
        log("stopping")
    finally:
        server.shutdown()
        for proc in (tunnel.proc if tunnel else None, ollama_proc):
            if proc is not None and proc.poll() is None:
                proc.terminate()


if __name__ == "__main__":
    sys.exit(main())

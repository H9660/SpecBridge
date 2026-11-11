"""The Jira trigger service (ADR D28): a "Run SpecBridge" button in Jira starts a live run.

A Jira Automation rule (manual trigger) sends POST /run {"key": "SPEC-66"} with the header X-SpecBridge-Secret.
This service checks the request, queues the ticket and answers at once (202); one worker thread runs the queued
tickets one at a time with run_ticket(key, "live"), so the page and the Jira comment are written by the publish
node as on the command line. Standard library only.

Checks on every request: the path and method, the secret (compared in constant time), the size and type of the
body, a ticket key of the configured project; then: not already queued or running, not run in the last
ticket_cooldown_seconds, the queue not full, and the day's spending (finished runs + every queued or running run
at its cost cap) under daily_budget_usd.
The ticket's one [SpecBridge] comment says "generating..." at once; publish replaces it with the result; if the
run fails, it says so. In dry-run mode (for trying the service) nothing is written to Jira at all.
The queue and the day's spending are kept in data/service/ (a restart picks the queue up again); the log holds
ticket keys and outcomes, never the secret or the request headers.
"""
import hmac
import json
import logging
import math
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from specbridge import ticket_text
from specbridge.agent import run_record
from specbridge.agent.nodes import publish
from specbridge.agent.nodes.clarify import COMMENT_MARKER
from specbridge.env import PROJECT

STATE_DIR = PROJECT / "data" / "service"
SECRET_ENV = "SPECBRIDGE_WEBHOOK_SECRET"
SECRET_HEADER = "X-SpecBridge-Secret"
MIN_SECRET_CHARS = 24
MAX_BODY = 4096
TICKET_KEY = re.compile(r"[A-Z][A-Z0-9]{1,9}-\d{1,7}")
BUTTON = "Actions -> Run SpecBridge"

STARTED = ("{marker} {key}: Generating UAT test cases for PM and engineering review\n"
           "SpecBridge is reading the ticket and the code. This usually takes 2-5 minutes; this comment will be "
           "updated with a link to the UAT page.{queued}")
FAILED = ("{marker} {key}: UAT test cases could not be generated this time\n"
          "Reason: {reason}\n"
          "Nothing was published. Use " + BUTTON + " to try again later.")
LIMIT = ("{marker} {key}: Not started - the daily SpecBridge limit is reached\n"
         "Use " + BUTTON + " again tomorrow.")

log = logging.getLogger("specbridge.service")


class ServiceError(RuntimeError):
    pass


def _short(reason):
    """A reason safe to show on a ticket: one line, no secrets, at most 200 characters."""
    text = " ".join(ticket_text.redact_secrets(str(reason or "unknown error"))[0].split())
    return text if len(text) <= 200 else text[:199] + "…"


class Service:
    """The queue, the worker and the Jira comments. `runner(key, run_id)` returns a RunResult (tests pass a fake);
    `client` is the Atlassian client for the comments (None: built from env when first needed)."""

    def __init__(self, env, settings, runner=None, client=None, state_dir=STATE_DIR, records_dir=run_record.RUNS,
                 dry_run=False, clock=time.time):
        self.secret = env.get(SECRET_ENV) or ""
        if len(self.secret) < MIN_SECRET_CHARS:
            raise ServiceError(f"{SECRET_ENV} in .env must be set to a random string of at least {MIN_SECRET_CHARS} "
                               "characters (see .env.example)")
        self.project = env.get("JIRA_PROJECT_KEY") or ""
        if not self.project:
            raise ServiceError("JIRA_PROJECT_KEY is not set in .env")
        self.env, self.settings, self.clock = env, settings, clock
        self.mode = "dry-run" if dry_run else "live"
        self.records_dir, self.state_dir = records_dir, state_dir
        self.runner = runner or self._run_ticket
        self._client = client
        self.lock = threading.Condition()
        self.stopping = False
        state_dir.mkdir(parents=True, exist_ok=True)
        saved = self._load("queue.json", {})
        self.queue = list(dict.fromkeys(([saved["running"]] if saved.get("running") else []) + saved.get("queue", [])))
        self.running = None
        self.ledger = self._load("ledger.json", {})
        self._roll_day()
        self._save_queue()

    # --- small files in data/service ---

    def _load(self, name, default):
        try:
            return json.loads((self.state_dir / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    def _save(self, name, data):
        tmp = self.state_dir / f".{name}.tmp"
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.state_dir / name)

    def _save_queue(self):
        self._save("queue.json", {"running": self.running, "queue": self.queue})

    def _roll_day(self):
        day = time.strftime("%Y-%m-%d", time.gmtime(self.clock()))
        if self.ledger.get("day") != day:
            self.ledger = {"day": day, "spent_usd": 0.0, "runs": 0, "last_run": self.ledger.get("last_run", {})}
            self._save("ledger.json", self.ledger)

    # --- Jira comments (never in dry-run) ---

    def client(self):
        if self._client is None:
            from specbridge.atlassian import Atlassian
            self._client = Atlassian(self.env)
        return self._client

    def comment(self, key, text):
        if self.mode != "live":
            log.info("%s: (dry-run, not posted) %s", key, text.splitlines()[0])
            return
        try:
            publish.put_comment(self.client(), key, text, "")
        except Exception as err:  # noqa: BLE001 - a comment that fails must not stop the run or the service
            log.warning("%s: could not update the Jira comment: %s", key, _short(err))

    # --- requests ---

    def submit(self, key):
        """(HTTP status, answer) for a checked ticket key of this project."""
        now = self.clock()
        with self.lock:
            self._roll_day()
            if key == self.running or key in self.queue:
                return 200, {"queued": False, "reason": f"{key} is already queued or running"}
            wait = self.settings.ticket_cooldown_seconds - (now - self.ledger["last_run"].get(key, float("-inf")))
            if wait > 0:
                return 429, {"queued": False, "reason": f"{key} ran recently; try again in {math.ceil(wait / 60)} min"}
            if len(self.queue) >= self.settings.queue_max:
                return 429, {"queued": False, "reason": "the queue is full; try again later"}
            committed = self.ledger["spent_usd"] + self.settings.cost_cap_usd * (len(self.queue) + bool(self.running))
            over = committed + self.settings.cost_cap_usd > self.settings.daily_budget_usd
            if not over:
                self.queue.append(key)
                self._save_queue()
                ahead = len(self.queue) - 1 + bool(self.running)
                self.lock.notify_all()
        if over:
            log.info("%s: refused, daily limit $%.2f reached", key, self.settings.daily_budget_usd)
            self.comment(key, LIMIT.format(marker=COMMENT_MARKER, key=key))
            return 429, {"queued": False, "reason": "the daily SpecBridge limit is reached"}
        log.info("%s: queued (%d ahead)", key, ahead)
        queued = f"\n(Queued behind {ahead} other ticket{'s' if ahead != 1 else ''}.)" if ahead else ""
        self.comment(key, STARTED.format(marker=COMMENT_MARKER, key=key, queued=queued))
        return 202, {"queued": True, "position": ahead + 1}

    # --- the worker ---

    def start(self):
        thread = threading.Thread(target=self.work, name="specbridge-worker", daemon=True)
        thread.start()
        return thread

    def stop(self):
        with self.lock:
            self.stopping = True
            self.lock.notify_all()

    def work(self):
        while True:
            with self.lock:
                while not self.queue and not self.stopping:
                    self.lock.wait(timeout=1)
                if self.stopping:
                    return
                key = self.queue.pop(0)
                self.running = key
                self._save_queue()
            cost = self.run_one(key)
            with self.lock:
                self._roll_day()
                self.running = None
                self.ledger["spent_usd"] = round(self.ledger["spent_usd"] + cost, 6)
                self.ledger["runs"] += 1
                self.ledger["last_run"][key] = self.clock()
                self._save("ledger.json", self.ledger)
                self._save_queue()
                self.lock.notify_all()

    def run_one(self, key):
        """Run one ticket; returns its cost. Any failure ends in a comment, never in a stopped service."""
        from specbridge.agent.graph import new_run_id
        run_id = new_run_id()
        log.info("%s: run %s started (%s)", key, run_id, self.mode)
        try:
            result = self.runner(key, run_id)
            state = result.state or {}
            problem = (state.get("published") or {}).get("error") or (state.get("saved") or {}).get("error")
            if problem:
                self.comment(key, FAILED.format(marker=COMMENT_MARKER, key=key, reason=_short(problem)))
            log.info("%s: run %s %s%s", key, run_id, result.status, f" - {_short(problem)}" if problem else "")
        except Exception as err:  # noqa: BLE001 - the run record is already written by run_ticket
            log.warning("%s: run %s failed: %s", key, run_id, _short(f"{type(err).__name__}: {err}"))
            self.comment(key, FAILED.format(marker=COMMENT_MARKER, key=key, reason=_short(err)))
        record = run_record.path_for({"run_id": run_id, "ticket": {"key": key}}, self.records_dir)
        try:
            cost = float(json.loads(record.read_text(encoding="utf-8")).get("spent", {}).get("cost", 0.0))
        except (OSError, ValueError, TypeError):
            cost = 0.0      # no record: the run was refused before it existed, so no AI call was made
        return cost

    def _run_ticket(self, key, run_id):
        from specbridge.agent.graph import run_ticket
        return run_ticket(key, self.mode, run_id, settings=self.settings, records_dir=self.records_dir)

    def status(self):
        with self.lock:
            return {"ok": True}


def make_handler(service):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SpecBridge"
        sys_version = ""

        def _send(self, code, body):
            data = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            log.info("%s %s %s -> %d", self.client_address[0], self.command, self.path.split("?")[0][:40], code)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, service.status())
            if self.path == "/run":
                return self._send(405, {"error": "use POST"})
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/run":
                return self._send(404, {"error": "not found"})
            given = self.headers.get(SECRET_HEADER, "")
            if not hmac.compare_digest(given.encode("utf-8"), service.secret.encode("utf-8")):
                return self._send(401, {"error": "missing or wrong secret"})
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length > MAX_BODY:
                return self._send(413, {"error": f"the body may be at most {MAX_BODY} bytes"})
            if length <= 0:
                return self._send(400, {"error": "a JSON body {\"key\": \"<ticket key>\"} is needed"})
            if not (self.headers.get("Content-Type") or "").lower().startswith("application/json"):
                self.rfile.read(length)
                return self._send(415, {"error": "the body must be application/json"})
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return self._send(400, {"error": "the body is not valid JSON"})
            key = body.get("key") if isinstance(body, dict) else None
            key = key.strip().upper() if isinstance(key, str) else ""
            if not TICKET_KEY.fullmatch(key):
                return self._send(400, {"error": "\"key\" must be a ticket key such as SPEC-12"})
            if key.split("-")[0] != service.project:
                return self._send(403, {"error": f"only tickets of project {service.project} can be run"})
            code, answer = service.submit(key)
            return self._send(code, answer)

        def _not_allowed(self):
            return self._send(405, {"error": "method not allowed"})

        do_PUT = do_DELETE = do_PATCH = _not_allowed

        def log_message(self, fmt, *args):   # the default logs to stderr with the full request line; _send logs instead
            pass

    return Handler


def make_server(service, host="127.0.0.1", port=8765):
    return ThreadingHTTPServer((host, port), make_handler(service))

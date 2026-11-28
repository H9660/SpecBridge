"""The SLM host pool (ADR D31): any number of SLM hosts (scripts/slm_host.py), shared by every SLM brain in a process.

The SLM brain (brain.py SLMHostBrain) asks the pool for a host before each job and gives it back after. The pool:
  - knows each host's state: healthy | down | misconfigured | unknown (not checked yet);
  - picks the least-loaded healthy host that serves the model, holding at most `jobs_per_host` of this process's jobs
    per host; load = this process's jobs on it + the jobs other processes had there at its last status check;
  - makes callers wait in a first-in, first-out queue when every host is busy;
  - checks a host's GET /v1/status every `health_seconds`, and a down or misconfigured one again after
    `retry_down_seconds` (every few seconds while no host at all is usable);
  - marks a host down after `down_after_failures` failed requests in a row, and healthy again when one works.
What to do with a job when its host fails (send it elsewhere, retry, give up) is the brain's part.

Settings: SLM_BASE_URLS="name=https://a.trycloudflare.com/v1,https://b.../v1" (names optional), or SLM_BASE_URL for
one host; the `pool` block of the slm profile in config/brains.json. Standard library only.
"""
import collections
import itertools
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.request

from specbridge.env import PROJECT

BRAINS = PROJECT / "config" / "brains.json"
DEFAULTS = {"jobs_per_host": 1, "health_seconds": 15, "down_after_failures": 2, "retry_down_seconds": 30,
            "busy_seconds": 5, "all_down_probe_seconds": 5}
HEALTHY, DOWN, MISCONFIGURED, UNKNOWN = "healthy", "down", "misconfigured", "unknown"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,39}")
PROBE_SECONDS = 10
progress = logging.getLogger("specbridge.progress")   # silent unless the caller adds a handler (run_ticket.py does)


class PoolError(RuntimeError):
    """No host can take the job. kind: "key" (every host refused the key), "model" (no host serves the model),
    "unreachable" (no host answered for the caller's patience), "busy" (no host was free before the deadline)."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


# --- settings ---------------------------------------------------------------------------------------------------

def api_root(url, name):
    """A host address with or without /v1, as the address with /v1. ValueError if it is not http(s)."""
    url = url.strip().rstrip("/")
    if not re.match(r"https?://[^/\s]+", url):
        raise ValueError(f"{name} must hold http(s) addresses, like https://example.trycloudflare.com/v1; got {url!r}")
    return url if url.endswith("/v1") else url + "/v1"


def parse_hosts(value, env_name="SLM_BASE_URLS"):
    """[(name, url)] from "name=url,url,...": any number of hosts; unnamed ones are called host-1, host-2, ..."""
    hosts = []
    for i, item in enumerate((x.strip() for x in (value or "").split(",")), 1):
        if not item:
            continue
        name, sep, url = item.partition("=")
        if not sep or name.lower().startswith("http"):
            name, url = f"host-{i}", item
        name = name.strip()
        if not NAME.fullmatch(name):
            raise ValueError(f"{env_name}: host name {name!r} may only use letters, digits, '.', '_' and '-'")
        hosts.append((name, api_root(url, env_name)))
    if not hosts:
        raise ValueError(f"{env_name} is set but holds no address")
    for kind, values in (("name", [n for n, _ in hosts]), ("address", [u for _, u in hosts])):
        twice = sorted({v for v in values if values.count(v) > 1})
        if twice:
            raise ValueError(f"{env_name} names the same host {kind} twice: {', '.join(twice)}")
    return hosts


def pool_settings(profile=None):
    return {**DEFAULTS, **((profile or {}).get("pool") or {})}


def auto_concurrency(env, max_workers, config_path=BRAINS):
    """max_concurrency "auto": the SLM hosts x jobs_per_host, at most max_workers (a broken list counts as 1 host;
    load_brain reports it)."""
    try:
        hosts = len(parse_hosts(env.get("SLM_BASE_URLS"))) if env.get("SLM_BASE_URLS") else 1
    except ValueError:
        hosts = 1
    try:
        profile = json.loads(config_path.read_text(encoding="utf-8"))["brains"]["slm"]
    except (OSError, KeyError, ValueError):
        profile = {}
    return max(1, min(max_workers, hosts * int(pool_settings(profile)["jobs_per_host"])))


# --- one host ---------------------------------------------------------------------------------------------------

class Host:
    def __init__(self, name, url):
        self.name, self.url = name, url.rstrip("/")
        self.state, self.reason = UNKNOWN, "not checked yet"
        self.failures = 0             # failed requests in a row
        self.checked = 0.0            # time of the last status check (probe)
        self.last_seen = None         # time of the last answer of any kind
        self.inflight = 0             # this process's jobs on this host now
        self.others = 0               # jobs of other processes at the last status check
        self.models = None            # models it has pulled (None: not known, e.g. an older host)
        self.missing = set()          # models it refused to serve
        self.status = {}              # its last /v1/status answer
        self.rtt_ms = None
        self.picked = 0               # round-robin order among equally loaded hosts
        self.busy_until = 0.0         # skip after a "queue full" answer
        self.key_refused = False
        self.probing = False
        self.answers = self.errors = 0

    def serves(self, model):
        return model not in self.missing and (self.models is None or model is None or model in self.models)

    def view(self, with_url=True):
        now = time.time()
        out = {"name": self.name, "state": self.state, "reason": "" if self.state == HEALTHY else self.reason,
               "queued": self.status.get("queued"), "running": self.status.get("running"),
               "ready": self.status.get("ready"), "version": self.status.get("version"),
               "host_name": self.status.get("name"), "in_flight_here": self.inflight,
               "answers_here": self.answers, "errors_here": self.errors,
               "last_seen_seconds": None if self.last_seen is None else round(now - self.last_seen, 1),
               "rtt_ms": self.rtt_ms, "models": sorted(self.models) if self.models is not None else None}
        if with_url:
            out["url"] = self.url
        return out


# --- the pool ---------------------------------------------------------------------------------------------------

class HostPool:
    def __init__(self, hosts, key, settings=None, env_name="SLM_BASE_URLS", opener=None):
        if not hosts:
            raise ValueError("an SLM host pool needs at least one host")
        self.hosts = [Host(n, u) for n, u in hosts]
        self.key, self.env_name = key, env_name
        self.settings = {**DEFAULTS, **(settings or {})}
        self.cond = threading.Condition()
        self.waiting = collections.deque()
        self.events = collections.deque(maxlen=5000)
        self._order = itertools.count(1)
        self._open = opener or urllib.request.urlopen

    def __repr__(self):
        return f"<HostPool {', '.join(h.name + ':' + h.state for h in self.hosts)}>"

    # --- events ---

    def event(self, kind, host, detail="", log=True):
        """Record what happened (the run record keeps it); state changes and moves also go to the progress log."""
        self.events.append({"t": round(time.time(), 3), "kind": kind, "host": host.name, "detail": detail})
        if log:
            progress.info("   SLM host %s %s%s", host.name, kind, f": {detail}" if detail else "")

    def _set(self, host, state, reason=""):
        """Change a host's state; a change is an event, except the first good check of a new host."""
        old = host.state
        host.state, host.reason = state, reason
        if old != state and not (old == UNKNOWN and state == HEALTHY):
            self.event("back" if state == HEALTHY else state, host, reason)
        self.cond.notify_all()

    # --- what the brain reports (all thread-safe) ---

    def ok(self, host):
        """A request to the host worked."""
        with self.cond:
            host.failures, host.last_seen = 0, time.time()
            if host.state in (DOWN, UNKNOWN):
                self._set(host, HEALTHY)

    def answered(self, host):
        with self.cond:
            host.answers += 1
            self.event("answer", host, log=False)

    def failed(self, host, reason):
        """A request failed (no answer, tunnel error, Ollama error); down after `down_after_failures` in a row."""
        with self.cond:
            host.failures += 1
            host.errors += 1
            if host.failures >= self.settings["down_after_failures"] and host.state != DOWN:
                host.checked = time.time()
                self._set(host, DOWN, reason)
            else:
                host.reason = reason

    def down(self, host, reason):
        """The host stopped answering during a job (after the caller's patience): down at once."""
        with self.cond:
            host.failures = max(host.failures, self.settings["down_after_failures"])
            host.errors += 1
            host.checked = time.time()
            self._set(host, DOWN, reason)

    def busy(self, host):
        """The host said its queue is full (503): skipped for a few seconds, not counted as a failure."""
        with self.cond:
            host.busy_until = time.time() + self.settings["busy_seconds"]
            self.event("busy", host, "its queue is full", log=False)
            self.cond.notify_all()

    def misconfigured(self, host, reason, model=None, key=False):
        """The host refused the key, or does not serve `model` (then only that model is avoided there)."""
        with self.cond:
            host.checked = time.time()
            if model is not None:
                host.missing.add(model)
                self.event("misconfigured", host, reason)
                self.cond.notify_all()
                return
            host.key_refused = key
            self._set(host, MISCONFIGURED, reason)

    def moved(self, job_id, old, new, why):
        with self.cond:
            self.event("moved", new, f"job {job_id[:8]} from {old} ({why})")

    # --- status checks (network; never under the lock) ---

    def _request(self, url, auth=True):
        headers = {"Authorization": f"Bearer {self.key}"} if auth and self.key else {}
        req = urllib.request.Request(url, headers=headers)
        with self._open(req, timeout=PROBE_SECONDS) as resp:
            return json.load(resp)

    def probe(self, host):
        """GET /v1/status (older hosts without it: GET /health) and update the host's state."""
        start = time.time()
        try:
            try:
                status = self._request(host.url + "/status")
            except urllib.error.HTTPError as err:
                if err.code != 404:
                    raise
                root = host.url[:-3] if host.url.endswith("/v1") else host.url
                status = {"legacy": True, **self._request(root + "/health", auth=False)}
        except urllib.error.HTTPError as err:
            with self.cond:
                host.probing = False
                if err.code in (401, 403):
                    self.misconfigured(host, f"refused the key (HTTP {err.code})", key=True)
                else:
                    self._probe_failed(host, f"HTTP {err.code}")
            return
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as err:
            with self.cond:
                host.probing = False
                self._probe_failed(host, str(getattr(err, "reason", None) or err) or type(err).__name__)
            return
        with self.cond:
            now = time.time()
            host.probing, host.checked, host.last_seen = False, now, now
            host.rtt_ms = round((now - start) * 1000)
            host.status = status if isinstance(status, dict) else {}
            models = host.status.get("models")
            host.models = ({m for m, v in models.items() if isinstance(v, dict) and v.get("pulled")}
                           if isinstance(models, dict) else None)
            host.missing -= host.models or set()
            load = (host.status.get("queued") or 0) + (host.status.get("running") or 0)
            host.others = max(0, load - host.inflight)
            host.key_refused = False
            if host.status.get("ollama") is False:
                self._probe_failed(host, "its Ollama is not answering")
            else:
                host.failures = 0
                self._set(host, HEALTHY)

    def _probe_failed(self, host, reason):
        host.checked = time.time()
        host.failures += 1
        self._set(host, DOWN, reason)

    def _due(self, host, now, none_usable):
        if host.probing:
            return False
        if host.state == UNKNOWN:
            return True
        if host.state == HEALTHY:
            return now - host.checked >= self.settings["health_seconds"]
        wait = self.settings["all_down_probe_seconds"] if none_usable else self.settings["retry_down_seconds"]
        return now - host.checked >= min(wait, self.settings["retry_down_seconds"])

    def refresh(self, force=False):
        """Check every host that is due (all of them with force), in parallel; returns when they are done."""
        with self.cond:
            now = time.time()
            none_usable = not any(h.state == HEALTHY for h in self.hosts)
            due = [h for h in self.hosts if (force and not h.probing) or self._due(h, now, none_usable)]
            for h in due:
                h.probing = True
        threads = [threading.Thread(target=self.probe, args=(h,), daemon=True) for h in due]
        for t in threads:
            t.start()
        for t in threads:
            t.join(PROBE_SECONDS + 5)

    # --- picking a host ---

    def _pick(self, model, avoid, now):
        free = [h for h in self.hosts if h.state == HEALTHY and h.serves(model) and h.busy_until <= now
                and h.inflight < self.settings["jobs_per_host"]]
        preferred = [h for h in free if h.name not in avoid] or free
        if not preferred:
            return None
        return min(preferred, key=lambda h: (h.inflight + h.others, h.picked))

    def _hopeless(self, model):
        """A PoolError if no host could ever take this job without someone fixing it, else None."""
        serving = [h for h in self.hosts if h.serves(model)]
        if not serving:
            return PoolError("model", f"no SLM host serves {model}: " + self.summary())
        if all(h.state == MISCONFIGURED for h in serving):
            kind = "key" if all(h.key_refused for h in serving) else "model"
            return PoolError(kind, "every SLM host is misconfigured: " + self.summary())
        return None

    def acquire(self, model, deadline, patience, avoid=()):
        """A host for one job of `model`, counted as this process's until release(). Prefers hosts not in `avoid`.
        Waits first-in, first-out while every host is busy (until `deadline`) or down (for `patience` seconds)."""
        ticket = object()
        with self.cond:
            self.waiting.append(ticket)
        unreachable_since = None
        try:
            while True:
                self.refresh()
                with self.cond:
                    now = time.time()
                    host = self._pick(model, set(avoid), now) if self.waiting[0] is ticket else None
                    if host is not None:
                        host.inflight += 1
                        host.picked = next(self._order)
                        self.waiting.popleft()
                        self.cond.notify_all()
                        return host
                    hopeless = self._hopeless(model)
                    if hopeless:
                        raise hopeless
                    if any(h.state in (HEALTHY, UNKNOWN) and h.serves(model) for h in self.hosts):
                        unreachable_since = None
                    else:
                        unreachable_since = unreachable_since or now
                        if now - unreachable_since >= patience:
                            raise PoolError("unreachable", self.summary())
                    if now >= deadline:
                        raise PoolError("busy", f"no SLM host was free in time: {self.summary()}")
                    self.cond.wait(timeout=max(0.02, min(1.0, deadline - now)))
        finally:
            with self.cond:
                if ticket in self.waiting:
                    self.waiting.remove(ticket)
                    self.cond.notify_all()

    def release(self, host):
        with self.cond:
            host.inflight = max(0, host.inflight - 1)
            self.cond.notify_all()

    # --- reports ---

    def summary(self):
        """One line per host for error messages: 'kaggle-a down: timed out; kaggle-b healthy'."""
        return "; ".join(f"{h.name} {h.state}" + (f": {h.reason}" if h.state != HEALTHY and h.reason else "")
                         for h in self.hosts)

    def status(self, with_url=True):
        with self.cond:
            return [h.view(with_url) for h in self.hosts]

    def report_since(self, since):
        """For the run record: answers per host and the pool's events (state changes, moves) since `since`."""
        with self.cond:
            events = [e for e in self.events if e["t"] >= (since or 0)]
            answers = collections.Counter(e["host"] for e in events if e["kind"] == "answer")
            return {"hosts": [h.view(with_url=False) for h in self.hosts], "answers_by_host": dict(answers),
                    "events": [e for e in events if e["kind"] != "answer"]}


# --- one pool per set of hosts, per process ---------------------------------------------------------------------

_POOLS, _POOLS_LOCK = {}, threading.Lock()


def get_pool(hosts, key, settings=None, env_name="SLM_BASE_URLS"):
    """The process's pool for these hosts and key (every brain and thread shares it)."""
    k = (tuple(tuple(h) for h in hosts), key)
    with _POOLS_LOCK:
        if k not in _POOLS:
            _POOLS[k] = HostPool(hosts, key, settings, env_name)
        return _POOLS[k]


def all_pools():
    with _POOLS_LOCK:
        return list(_POOLS.values())


def reset_pools():
    """Forget every pool (tests)."""
    with _POOLS_LOCK:
        _POOLS.clear()


def health_report(env=None, with_url=True):
    """Every configured SLM host, checked now: {"brain", "hosts_env", "usable", "hosts": [view, ...]}.
    Used by scripts/slm_pool.py status and GET /slm/health on the Jira service. With BRAIN other than slm: no hosts."""
    from specbridge.brain import load_brain     # here, not at the top: brain.py imports this module
    from specbridge.env import load_env
    env = load_env() if env is None else env
    if (env.get("BRAIN") or "llm") != "slm":
        return {"brain": env.get("BRAIN") or "llm", "hosts_env": None, "usable": 0, "hosts": []}
    brain = load_brain(env=env)
    pool = brain.pool()
    pool.refresh(force=True)
    hosts = pool.status(with_url)
    return {"brain": "slm", "hosts_env": pool.env_name, "usable": sum(h["state"] == HEALTHY for h in hosts),
            "hosts": hosts}


def report_since(since):
    """The run record's `slm_pool` part: every pool this process used, or None if it used none."""
    pools = all_pools()
    if not pools:
        return None
    reports = [p.report_since(since) for p in pools]
    return reports[0] if len(reports) == 1 else {"pools": reports}

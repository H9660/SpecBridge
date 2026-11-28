# D31 - The SLM brain uses a pool of any number of SLM hosts: the client picks a host, fails over, and queues

- **Status:** Accepted
- **Date:** 2026-11-27
- **Decided by:** the user, 2026-11-27: asked for it ("horizontally scale the SLMs over several Kaggle notebooks; handle failures, retries and health checks; any number of servers"), accepted the design with one change (`retry_down_seconds` 30, not 60), and asked for it to be built.
- **Related:** [D29](0029-slm-brain-on-kaggle-host.md) (the single SLM host, jobs, polling), [D28](0028-jira-button-webhook-service.md) (the Jira service), ARCHITECTURE.md D9 (limits), D19 (workers one at a time on the SLM); USER_CLARIFICATIONS.md 2026-11-27; `specbridge/brain.py` (`SLMHostBrain`), `scripts/slm_host.py`, `config/brains.json` (`slm`), `config/agent.json` (`max_concurrency`), `specbridge/agent/preflight.py`, `specbridge/service.py`, `docs/DEPLOY_SLM.md`

## Context

Today the SLM brain talks to one host: one Kaggle notebook (2× T4) behind one tunnel (D29).

- **It is slow.** The host runs one job at a time, so `max_concurrency` for the SLM is 1, and the workers run one after another. A ticket takes about 5-15 minutes (SPEC-1: about 6 minutes).
- **It is fragile.** If that notebook stops, every run fails until someone restarts it and copies the new address into `.env`.
- **It cannot grow.** The user has 3 Kaggle notebooks available now, and wants any number later.

What already exists and is kept:

| Already there (D29) | Why it helps a pool |
|---|---|
| Answers are jobs with an id the client picks | A job can be sent again, to the same host or another one, without a mix-up |
| Sending the same id twice runs it once (per host) | A lost answer costs only a retry |
| Every request carries the whole conversation | Any host can answer any call; no host keeps a worker's state |
| Each host has its own queue and answers `503` when full | A full host can be skipped |
| `GET /health` on each host | A liveness check already exists |

## Decision

### 1. Shape: the pool lives in the client, not in a proxy

```
Laptop process (run_ticket.py or serve.py)
  LangGraph: up to N workers at once (N = number of hosts, "auto")
     │  each brain call
     ▼
  SLMHostBrain ──► HostPool (one per process, shared by all threads)
                    • knows every host: state, queue depth, jobs in flight
                    • picks a host, waits in a local queue if all are busy
                    • probes health, takes down hosts out, lets them back in
     │ POST /v1/jobs, GET /v1/jobs/<id>           (to the chosen host only)
     ├──────────────► https://a.trycloudflare.com  Kaggle notebook A (slm_host.py --name kaggle-a)
     ├──────────────► https://b.trycloudflare.com  Kaggle notebook B
     └──────────────► https://c.trycloudflare.com  Kaggle notebook C  ... any number
```

There is no extra server. Every process that uses the SLM brain builds its own pool from the same settings. The hosts' own queue counts (from `/v1/status`) are the shared truth when two processes, such as `serve.py` and a `run_ticket.py`, use the hosts at the same time.

### 2. Settings

| Setting | Where | Meaning |
|---|---|---|
| `SLM_BASE_URLS` | `.env` | Comma-separated host addresses, any number. Each one may have a name: `kaggle-a=https://a.trycloudflare.com/v1`. |
| `SLM_BASE_URL` | `.env` | Still works, as a pool of one host. If both are set, `SLM_BASE_URLS` wins and preflight warns. |
| `SLM_API_KEY` | `.env` | One key, shared by every host (the same Kaggle secret in every notebook). |
| `pool.jobs_per_host` | `brains.json` `slm` | How many of this process's jobs a host may hold at once (queued + running). Default **1**, because each host runs one job at a time. |
| `pool.health_seconds` | same | How old a host's status may be before it is checked again. Default **15**. |
| `pool.down_after_failures` | same | Failed requests in a row before a host is marked down. Default **2**. |
| `pool.retry_down_seconds` | same | How long a down host is skipped before it is probed again. Default **30**. |
| `max_concurrency.slm` | `agent.json` | New value **`"auto"`** = number of configured hosts × `jobs_per_host`, never more than `max_workers`. A number still works. |

The existing `timeout_seconds` (1,800), `unreachable_seconds` (120), `poll_seconds` (2) and `http_retries` (2) keep their meaning, but now for the whole call across all hosts.

### 3. Host states

| State | Meaning | Gets new jobs? |
|---|---|---|
| `healthy` | Its last request or probe worked | Yes |
| `down` | `down_after_failures` requests in a row failed (no answer, tunnel error 52x, Ollama 5xx) | No. It is probed again after `retry_down_seconds`, and is `healthy` again when the probe works. |
| `misconfigured` | It refused the key (401) | No. It is checked again after `retry_down_seconds`, so a fixed key is picked up without a restart. If every host is misconfigured, a call fails at once instead of waiting. |
| `unknown` | Not checked yet (start-up) | After its first probe |

A host that lacks one model (its `/v1/status` does not list it as pulled, or it refused a job with "not served") is left out for that model only.

### 4. Picking a host for a call

1. Keep the hosts that are `healthy`, serve the model the call needs, and hold fewer than `jobs_per_host` of this process's jobs.
2. Among them, pick the one with the fewest jobs waiting. Waiting = the host's last reported `queued + running`, plus this process's jobs sent since that report. A tie goes round-robin.
3. If none is free, the call **waits in a local queue** (first in, first out) until a slot frees or a down host comes back. Waiting counts against the call's `timeout_seconds`.

So there are three layers of queueing, each with a limit:

| Layer | Limit | When full |
|---|---|---|
| LangGraph (`max_concurrency`) | workers running at once | the next worker starts when one ends |
| Pool's local queue | `timeout_seconds` per call | the call fails: "no SLM host was free within N s" |

A down host is checked every `retry_down_seconds` (30 s). While no host at all is usable, the waiting calls check the down hosts every 5 s, so a notebook that comes back is used quickly.
| Each host's queue (`MAX_JOBS`) | jobs held by the host | `503`: that host is skipped and the next one is tried |

### 5. Failures and retries

A job keeps its id while it moves between hosts, so a host that still has it runs it once. A retry after a job *ended* in an error uses a new id, because the host keeps the finished job (and its error) under the old one.

| What happens | What the pool does |
|---|---|
| **Submit fails** (no answer, 52x, timeout) | Counts a failure for that host, then sends the job to the next host at once. |
| **Host is full** (`503` on submit) | Next host at once. It is not counted as a failure. |
| **Host stops answering while the job runs** | Keeps polling the same host for up to `unreachable_seconds`, because the job is still there. After that the host is marked down and the job is sent to another host under the same id. If the first host comes back and finishes it, that answer is ignored. |
| **Host lost the job** (`GET` gives 404: it restarted) | Sent again under the same id: to the same host if it is healthy, else to another one. |
| **Job ends in error 5xx** (Ollama crashed or hung) | Retried on another host, up to `http_retries` times, with a back-off of 2, 4 ... 30 s. |
| **Job ends in `413`** (prompt too long) or **`400`** | Not retried. Every host has the same models and contexts, so another host would refuse it too. |
| **`401`** (wrong key) | That host becomes `misconfigured`, and the job goes to another host. If every host refuses the key, the call fails with the key error from D29. |
| **Every host is down** | Waits while probing, for up to `unreachable_seconds`, then fails: "no SLM host is reachable (3 configured: kaggle-a down: HTTP 530; kaggle-b down: timed out; kaggle-c refused the key)". |
| **The call's `timeout_seconds` runs out** | A job still queued on a host is cancelled (`DELETE`), as in D29, and the call fails. |

A brain call that fails still becomes an `incomplete` or `error` result in the graph, as today (D9). Nothing fails silently.

A known cost: a job resent after a host stopped answering may run twice, once on each host. It wastes GPU time but never gives a wrong answer, because only the first answer received is used.

### 6. Health endpoints

**On each host (`scripts/slm_host.py`):**

| Endpoint | Key needed | Answer |
|---|---|---|
| `GET /health` | no | `{"ok": true}`, unchanged. It shows only that the server is up and gives nothing away. |
| `GET /v1/status` (new) | yes | `{"name", "version", "uptime_seconds", "ready", "models": {name: {"context", "pulled"}}, "queued", "running", "done", "errors", "max_jobs", "gpu"}`. `ready` is true when Ollama answers and every model is pulled. |

A new host option, `--name` (default: the machine's name), labels the host in every log and status line.

**On the laptop:**

| Where | What |
|---|---|
| `scripts/slm_pool.py status` (new) | One row per host: name, state, queued / running, done / errors, last seen, round-trip time, models ready. `--watch` refreshes every 5 s. Exit code 0 if at least one host is healthy. |
| Preflight (START of every run) | Asks every host for its models (`GET /v1/models`, as D29 did for one host). It passes if at least one host has every model the run needs (main, worker and reviewer), and warns for each host that is left out and why. Fails only if none is usable. `run_ticket.py` prints the hosts and how many were usable. |
| `GET /slm/health` on `serve.py` (new) | The same table as JSON. It needs the service's secret header, because the service is reachable through a tunnel. Host addresses are shown only as their names. |
| Run record and progress log | Each answer records the host that gave it (`Reply.host`). Failovers and host state changes go into the run record (`pool_events`) and the progress log, e.g. `worker W2 -> kaggle-b (kaggle-a down)`. |

### 7. What is added, changed and removed

| | Component | Change |
|---|---|---|
| **Added** | `specbridge/slm_pool.py` | `HostPool` and `HostState`: settings parsing, picking a host, local queue, health probes, state changes. Thread-safe, one per process. Standard library only. |
| **Added** | `scripts/slm_pool.py` | The `status` command above. |
| **Added** | `tests/test_slm_pool.py`, `tests/conftest.py` | Tests with fake hosts (see section 8); a fresh pool for every test. |
| **Changed** | `specbridge/agent/console.py` | Host events (down, back, moved) get their own colours in the progress lines. |
| **Changed** | `specbridge/brain.py` `SLMHostBrain` | Each call asks the pool for a host, keeps its job on that host, and follows section 5. `Reply` gains `host`. One-host behaviour is the same as today. |
| **Changed** | `scripts/slm_host.py` | `GET /v1/status`, `--name`. Jobs, queue and keys are unchanged. |
| **Changed** | `specbridge/agent/limits.py`, `config/agent.json` | `max_concurrency` accepts `"auto"`. The `slm` value becomes `"auto"` (was 1). On the LLM brain, `"auto"` means `max_workers`. |
| **Changed** | `config/brains.json` `slm` | A `pool` block with the defaults in section 2. |
| **Changed** | `specbridge/agent/preflight.py` | Checks every host (section 6). |
| **Changed** | `specbridge/service.py` | `GET /slm/health`. |
| **Changed** | `specbridge/agent/run_record.py` | Writes `pool_events` and the host per answer. |
| **Changed** | docs | `DEPLOY_SLM.md` (one notebook per account, same key, list the addresses), `ARCHITECTURE.md` D19 note, `repo_map.md`, `.env.example`. |
| **Removed** | `max_concurrency.slm = 1` | Replaced by `"auto"`. With one host, `"auto"` is still 1, so nothing changes for a single notebook. |
| **Removed** | — | No component is removed. There is no proxy service to add or run. |

### 8. Tests (all offline, with fake hosts on local ports)

| Test | Checks |
|---|---|
| Settings | `SLM_BASE_URLS` with 1, 3 and 10 hosts, with and without names; bad address; `SLM_BASE_URL` alone still works; both set gives a warning |
| Spreading the load | 3 hosts, 3 calls at once: one per host; a 4th call waits in the local queue, then runs on the first free host |
| Least loaded | A host that reports 2 queued jobs (another process) is picked last |
| Submit fails | Host A gives no answer: the call ends on B; A is marked down after 2 failures |
| Host dies mid-job | A stops answering while polling: after `unreachable_seconds` the same job id runs on B, and a late answer from A is ignored |
| Host restarted | `GET` 404: the job is sent again under the same id |
| Full host | `503` on A: B is used, and A is not marked down |
| No retry | `413` and `400` fail at once, on one host only |
| Wrong key | 401 on A only: A is misconfigured, B answers; 401 on every host: the D29 key error |
| All down, then back | Fails with the per-host list after `unreachable_seconds`; a host that comes back within that time gets the call |
| Recovery | A down host is probed after `retry_down_seconds` and used again |
| Timeout | The local queue wait counts against `timeout_seconds`; a queued job is cancelled |
| Threads | 20 calls from 8 threads: no host ever holds more than `jobs_per_host` of this process's jobs; every call ends |
| Endpoints | Host `/v1/status` needs the key and shows the counts; `/health` shows nothing more; `slm_pool.py status` exit codes; `serve.py /slm/health` needs the secret |
| `"auto"` | `max_concurrency` = hosts × `jobs_per_host`, capped by `max_workers`; 1 host gives 1 |
| Unchanged | The existing `tests/test_slm_host.py` and the agent tests pass |

## Consequences

- **Faster tickets, within limits.** Only the workers run in parallel. `understand`, `orchestrator`, `merge`, the reviewer's calls and `render` still run one after another (the reviewer's per-criterion calls can spread over hosts too). A ticket with 3 workers should drop from about 6 minutes to about 3-4. That is an estimate, to be measured on SPEC-1 with 3 hosts.
- **More tickets at once.** Several runs through `serve.py` share the hosts. This is the bigger gain.
- **A host dying is no longer fatal.** The run carries on with the others. A run fails only when every host is down.
- **Same answers.** Every host runs the same models and contexts, so which host answers does not change the result beyond normal model randomness. Each answer records its host, so this can be checked.
- **More setup.** Each notebook prints a new address each session, so `.env` needs one line per host, updated after restarts. `slm_pool.py status` shows which address is stale.
- **Kaggle rules.** Kaggle allows one account per person. Each host must run on a different person's account (teammates), or on another GPU provider. Several accounts owned by one person risk a ban of all of them. The pool does not care where a host runs.
- **GPU hours.** Each account has its own weekly GPU quota, so three hosts give three times the hours, and a ticket uses hours on several accounts at once.

## Alternatives considered

- **A proxy service in front of the hosts** (one address for the brain). It adds a server and a tunnel to keep alive, plus a single point of failure, and it would forward every poll. The client already has job ids and retries. A proxy only pays off when many separate clients must share one queue; if that happens, `HostPool` can be moved behind an HTTP front without changing the hosts.
- **Plain round-robin, no health or load data.** Simple, but it keeps sending jobs to a dead or busy host. Picking the least-loaded healthy host costs one small request every 15 s per host.
- **Keep each worker on one host (affinity)** so Ollama can reuse the cached prompt prefix. It would be faster per turn, but it makes failover and load spreading harder. Left for later, once the pool works and the gain can be measured.
- **A different key per host.** More secure if one teammate's notebook leaks, but one more secret per host to copy. One shared key is chosen; per-host keys can be added later as `name=url|KEY_ENV`.
- **vLLM with built-in batching on each host.** It serves more parallel requests per GPU, but D29 rejected it (one model per process, three tunnels). Unchanged here.

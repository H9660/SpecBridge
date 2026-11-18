# SpecBridge on small language models (SLMs): report

**Date:** 2026-11-18. **Decision record:** [ADR D29](adr/0029-slm-brain-on-kaggle-host.md). **How to run it:** [DEPLOY_SLM.md](DEPLOY_SLM.md).

## 1. Summary

SpecBridge used to call one cloud model, Gemini. It now also runs fully on **three open small models** hosted on a free Kaggle GPU. Switching is one setting, `BRAIN=slm`; the agent's graph, prompts and checks are unchanged. A full ticket (SPEC-1) ran end to end in **about 6 minutes at $0.00**.

## 2. What we built

```
Laptop: SpecBridge (BRAIN=slm), code index, Jira
   │  submits each AI answer as a job, then asks for it every 2 s
   ▼
Cloudflare quick tunnel  (https://<random>.trycloudflare.com)
   ▼
Kaggle notebook, 2 × Tesla T4 GPU (16 GB each)
   scripts/slm_host.py: checks a secret key → Ollama with 3 models
```

| Role in SpecBridge | Model | Size | Why this model |
|---|---|---|---|
| Main model: understand the ticket, plan, write test cases, merge | `qwen2.5-coder:14b` | 9 GB | Strong at reading code; reliable JSON output; no hidden "thinking" |
| Worker search turns: pick the next tool | `qwen2.5-coder:7b` | 5 GB | Many short calls, so smaller and faster |
| Reviewer: checks the test cases | `llama3.1:8b` | 5 GB | A different model family from the writers, so it doesn't share their blind spots |

All three fit on the two GPUs at once, so no model is swapped out during a run.

**Design choices that keep it reliable:**

| Problem | Solution |
|---|---|
| Cloudflare cuts a request after about 100 s; long SLM answers take minutes | Each answer is a **job**: submit (instant), then poll every 2 s. Every request is short. |
| A dropped connection or a host restart | A job id sent twice runs once; a lost job is sent again; a host unreachable for 120 s gives a clear error, never a hang |
| Ollama silently cuts prompts longer than its context | The host sets each model's context size on every request. A prompt that can't fit is refused with an error, never cut. |
| Prompts were sized for Gemini's very large context | The worker's prompt sizes now come from the brain profile (smaller for the SLM) |
| Anyone with the tunnel address could use the GPU | Every request needs a secret key, compared in constant time |

## 3. Results

All runs: ticket SPEC-1 ("Patient search results unmount and remount on every keystroke"), dry-run mode (nothing published).

| Run | What changed | Time | Tokens | Cost | Code read by each worker | Test cases |
|---|---|---|---|---|---|---|
| 1 | First SLM run | 5 min 48 s | 91,440 | $0.00 | W1: 6, W2: 0, E2E: 0, retries: 0 and 0 | 3 |
| 2 | After the location fix (section 5) | 5 min 42 s | 100,588 | $0.00 | W1: 16, W2: 2, E2E: 0, retry: 4 | 4, all citing code |
| 3 | Same as run 2, Gemini key removed (proof run) | 5 min 38 s | 97,642 | $0.00 | W1: 17, W2: 2, E2E: 0, W1-R2: 15 | 3, all citing code |

**What the SLM did well (run 2):**
- **Understanding:** it found the ticket's 3 criteria. It marked AC2 as conflicting and set it aside for the product manager instead of guessing.
- **Code search:** it searched the right app, `esm-patient-search-app`, the same area as the files the real fix changed.
- **Honesty:** it marked AC3 (memory growth) as "untestable" with a reason, instead of inventing a test.
- **Grounding:** every test case cited code the worker had actually read (`grounded_cases` 1.0).

**Where it is weaker:**
- **AC1 stayed "weak".** After the retry round, the reviewer still said the expected results don't clearly state "results don't remount".
- **The end-to-end worker read no code** in its 4 tool calls, so no cross-criterion flow was written.
- **One irrelevant file** (a devtools component) was cited alongside the right ones.
- **No comparison with Gemini yet.** That is planned for Step 10.

**Speed:** we estimated 20-40 minutes per ticket. Measured: about 6 minutes for a ticket with 2 workers plus a retry round, against 2-5 minutes on Gemini.

## 4. Proof that it runs on the SLMs

| Evidence | What it shows |
|---|---|
| **Run record** (`data/runs/SPEC-1/<run>.json`) | Brain `slm`, provider `ollama`. Models per step: understand `qwen2.5-coder:14b`; worker search `qwen2.5-coder:7b`; writing `qwen2.5-coder:14b`; reviewer `llama3.1:8b`. Cost $0.00 for about 100k tokens. |
| **Kaggle cell log** | One line per AI answer computed on the T4 GPUs (model, time). Their timestamps match the run. `nvidia-smi` shows the GPU memory in use by Ollama. |
| **Gemini key removed** (run 3) | With `GEMINI_API_KEY` empty, SpecBridge cannot even create a Gemini brain ("brain 'llm' needs GEMINI_API_KEY"), yet the run still produced test cases. Run `20261118-182231-d475c7`: 3 test cases from llama3.1:8b, qwen2.5-coder:14b, qwen2.5-coder:7b in 5 min 38 s. |

## 5. Bugs found and fixed

| Bug | Found by | Fix |
|---|---|---|
| A small answer limit (`max_tokens=20`) was raised to 1,024 tokens | Live test with real Ollama on the laptop | The answer limit is only ever lowered to fit the context, never raised; regression test added |
| The 7b model split file locations at the wrong `/` (repo `core/packages/x`, path `src/a.ts`), so every file read failed and 4 of 5 workers read no code | First Kaggle run, then replaying one worker with logging | The tool runner joins the location and re-splits it at the real repo name (`fix_location`). Correct calls are unchanged, so Gemini is unaffected. Tests added. |
| The docs gave a `--dry-run` flag that doesn't exist | First laptop run | Corrected to `--mode dry-run` |

## 6. Changes to the codebase

| File | Change |
|---|---|
| `scripts/slm_host.py` (new) | The Kaggle host: installs Ollama, pulls and tests the models, runs the key-checking job server, opens the tunnel, restarts parts that stop. One file, standard library only. |
| `specbridge/brain.py` | New `SLMHostBrain` (submit a job, poll, retry, cancel), plus the `SLM_BASE_URL` setting |
| `config/brains.json` | The `slm` profile: the 3 models, key, polling, smaller prompt sizes |
| `config/agent.json`, `specbridge/agent/limits.py` | Any limit can be set per brain; the time cap is 600 s on Gemini and 3,600 s on the SLM |
| `specbridge/agent/worker/criterion_worker.py` | Prompt sizes come from the brain profile |
| `specbridge/agent/worker/tools.py` | `fix_location` for wrongly split file locations |
| `specbridge/agent/preflight.py` | Clear messages when the SLM host is down, refuses the key, or lacks a model |
| `specbridge/service.py` | The Jira "generating" comment says 5-15 minutes on the SLM |
| `specbridge/env.py`, `.env.example` | `SLM_BASE_URL` and `SLM_API_KEY` |
| `tests/test_slm_host.py` (new), `tests/agent/test_criterion_worker.py`, `tests/agent/test_start.py`, `scripts/smoke_test_step3.py` | 18 new host and brain tests, location-fix tests, updated brain checks |
| Docs | `DEPLOY_SLM.md` (new), ADR D29 (new), ARCHITECTURE, BUILD_STEPS, USER_CLARIFICATIONS, repo_map, CLAUDE.md |

In total: 19 files changed (about 250 lines added) plus 3 new files. No new packages; everything uses the Python standard library.

**Tests:** 416 pass. The only 2 failures (`test_clarify.py`) come from test fixtures that are not in git, and they fail the same way without these changes.

## 7. Limits and next steps

- **Manual steps each session:** a person starts the Kaggle notebook and pastes the new tunnel address into `.env`. Kaggle gives about 30 GPU hours a week, with sessions of up to 12 hours.
- **Quality:** run more tickets of different kinds on the SLM, and compare them with Gemini on the same golden tickets (Step 10).
- **Possible improvements:** give the end-to-end worker more tool calls on the SLM, or a prompt tuned for small models.

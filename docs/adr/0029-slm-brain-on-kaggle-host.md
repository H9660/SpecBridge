# D29 - The SLM brain: three small models on a Kaggle GPU, behind a key check, reached as polled jobs through a tunnel

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decided by:** the user. They asked for the SLM brain on 2-3 small models, hosted on Kaggle through Cloudflare, and left the choice of models, host software and reviewer family to Claude. The bar was "reliable, must not break the project".
- **Related:** ARCHITECTURE.md D1, D6, D8, D9, D19, section 3 (reviewer from a different family); [D23](0023-criterion-worker-design.md), [D25](0025-reviewer-flags-not-drops-one-retry.md), [D28](0028-jira-button-webhook-service.md); USER_CLARIFICATIONS.md 2026-11-18; `scripts/slm_host.py`, `specbridge/brain.py` (`SLMHostBrain`), `config/brains.json` (`slm`), `docs/DEPLOY_SLM.md`

## Context

The product must work with an SLM brain, with only the brain changing (two courses). The laptops have no NVIDIA GPU, and a 14B model on a laptop processor takes 10-20 minutes per ticket. Kaggle gives a free GPU machine (2× T4, 16 GB each, about 30 GPU hours a week, sessions of up to 12 hours), but it is not reachable from outside. The repo, code index and Jira service stay on the laptop.

Four problems had to be solved:

- **Cloudflare's time limit.** A Cloudflare quick tunnel ends a request after about 100 s without an answer (error 524). A long `write_cases` answer from a 14B model on a T4 can take minutes.
- **No login on Ollama.** Anyone with the tunnel address could use the GPU.
- **Silently cut prompts.** Ollama uses a small default context unless told otherwise, and cuts longer prompts without an error.
- **Prompts sized for Gemini.** `write_cases` could get about 25k tokens of input plus 8k of output.

## Decision

1. **The models** (each slot is one line in `config/brains.json`; the host's `--models` sets the context of each):

   | Slot | Nodes | Model | Context |
   |---|---|---|---|
   | main | understand, orchestrator, write_cases, e2e, merge | `qwen2.5-coder:14b` | 32,768 |
   | `worker_agent` | the worker's search turns (D23) | `qwen2.5-coder:7b` | 20,480 |
   | `reviewer` | reviewer (D25) | `llama3.1:8b`: another family, as ARCHITECTURE.md section 3 asks | 24,576 |

   Why these models:
   - None of them "thinks", so there is no hidden reasoning to cut off.
   - All handle JSON-schema output in Ollama.
   - Together they fit in 2× T4 (about 19 GB of weights), so no model is swapped out during a run.

2. **The host** (`scripts/slm_host.py`): one standard-library file, run in a Kaggle notebook.
   - It installs and starts Ollama, pulls the models, and loads each one with a test JSON answer.
   - It serves a small key-checking server on `127.0.0.1:8000`, the only thing the tunnel exposes. The key is compared in constant time, and only the configured models are accepted.
   - It starts a Cloudflare quick tunnel over http2, then restarts Ollama or the tunnel if either stops.

3. **Answers are jobs.** `SLMHostBrain` submits `POST /v1/jobs`, which answers at once, then polls `GET /v1/jobs/<id>` every 2 s. Every request is short, so the tunnel's limit never applies.
   - Sending the same job id twice runs it once. A job the host lost is sent again under its id.
   - Network and tunnel errors are retried until the host has been unreachable for 120 s, then the call fails with a clear error.
   - One call may take up to 1,800 s, queue time included. A job still waiting after that is cancelled.
   - The host runs jobs one at a time, in order.

4. **Context is set on every request.** The host calls Ollama's own API with each model's `num_ctx`, so nothing depends on Ollama's default. If the prompt leaves too little room, the answer limit is lowered, never below 1,024 tokens and never above what was asked. A prompt that cannot fit at all is refused with 413 instead of being cut.

5. **Prompt sizes follow the brain.** The profile keys `worker_context_cap` (12,000) and `evidence_chars` (32,000) replace the worker's fixed 15,000 / 48,000 for the SLM. `write_cases` then stays near 20k input tokens.

6. **Limits per brain** (`config/agent.json`): `time_cap_seconds` is 600 for the LLM and 3,600 for the SLM. Workers already run one at a time on the SLM (D19).

7. **Settings:** `BRAIN=slm`, `SLM_BASE_URL` (the address the host prints, with or without `/v1`) and `SLM_API_KEY`. `SLM_BASE_URL` belongs to the `slm` profile only, so it can never redirect the cloud brain. Real `SLM_*` environment variables override `.env`.

## Consequences

- Only the brain changes. The graph, prompts, nodes and checks are the same, and `BRAIN=llm` behaves as before.
- **Slower:** a ticket takes about 5-15 minutes on the SLM against 2-5 on Gemini. The first measured run, SPEC-1 on 2026-11-18, took about 6 minutes with 2 workers plus a retry round. It had been estimated at 20-40 minutes. The Jira comment says which.
- **First run found a small-model mistake:** `qwen2.5-coder:7b` split file locations at the wrong `/` (repo `core/packages/x`, path `src/a.ts`), so every `read_file` failed and 4 of 5 workers read no code. The tool runner now joins and re-splits the location at the real repo name (`tools.fix_location`); correct calls are unchanged. After the fix, the workers read 16, 2 and 4 pieces of code.
- **Cost:** none is reported (the Kaggle GPU is free), so `cost_usd` is empty and the cost cap never triggers. Time and the round limit still bound a run.
- **Token counts:** Ollama counts only the prompt tokens it had to process, so input tokens are lower when it reuses a cached prefix.
- **Manual steps:** a person must start the notebook and copy the new address into `.env` after every restart. Kaggle's weekly GPU hours limit how much evaluation can run.
- **Quality:** small models write weaker cases. The existing code checks (citations, criteria, injection) still apply unchanged, and Step 10 measures the difference.

## Alternatives considered

- **vLLM** has a built-in API key and is faster with many parallel requests. But it serves one model per process, so three models would need three servers and three tunnels, and our requests are one at a time anyway.
- **Ollama straight through the tunnel:** no key, and long answers hit the 100 s limit.
- **Streaming answers to beat the 100 s limit:** depends on Cloudflare passing bytes through without buffering, and a request waiting in the queue still sends nothing. Polling has neither problem.
- **Bigger models** (`mistral-small` 24B, `qwen3` 30B) would not fit next to two others, and models would be swapped in and out mid-run.
- **Thinking models** (`qwen3`) need thinking turned off reliably; the plain models avoid that risk.
- **Running on the laptop processor:** 10-20+ minutes per answer-heavy step. It is still possible for a quick test with `--no-install --no-tunnel`.

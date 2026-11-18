# Deploy: the SLM brain on a Kaggle GPU

This runs SpecBridge on three small models (SLMs) instead of Gemini. The models run on a free Kaggle GPU; SpecBridge stays on the laptop and reaches them through a Cloudflare tunnel. Design: [ADR D29](adr/0029-slm-brain-on-kaggle-host.md).

```
Laptop: SpecBridge (BRAIN=slm), code index, Jira service
   │  POST /v1/jobs, then GET /v1/jobs/<id> every 2 s     (every request is short)
   ▼
https://<random>.trycloudflare.com          (Cloudflare quick tunnel, no account needed)
   ▼
Kaggle notebook (GPU T4 x2)
   scripts/slm_host.py: key check on 127.0.0.1:8000  →  Ollama with 3 models
```

| Slot | Model | Used by |
|---|---|---|
| main | `qwen2.5-coder:14b` | understand, orchestrator, write_cases, e2e, merge |
| `worker_agent` | `qwen2.5-coder:7b` | the worker's search turns |
| `reviewer` | `llama3.1:8b` | the independent reviewer (a different family) |

## 1. One-time Kaggle setup

| Step | Where |
|---|---|
| Verify your phone number. Without it, notebooks get no internet or GPU. | kaggle.com → Settings → Phone verification |
| Make the shared secret on the laptop: `.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(32))"` | laptop |
| Store it in Kaggle as a secret named `SLM_API_KEY`. | Notebook → Add-ons → Secrets → Add secret, then tick it for this notebook |
| Put the same value in the laptop's `.env` as `SLM_API_KEY=...` | laptop |

## 2. Start the host (every session)

1. Create a new notebook. In the right-hand panel, set:
   - **Accelerator:** GPU T4 x2
   - **Internet:** on
2. Get `slm_host.py` into the notebook, in one of two ways:
   - **Upload it:** Add Input → Upload → New dataset → choose `scripts/slm_host.py`. Find its exact path with `!find /kaggle/input -name slm_host.py`. Newer Kaggle uses `/kaggle/input/datasets/<user>/<dataset>/slm_host.py`.
   - **Download it** (only if the repo is public and the file is pushed): `!wget -q https://raw.githubusercontent.com/H9660/SpecBridge/main/scripts/slm_host.py`
3. Run one cell:

   ```python
   from kaggle_secrets import UserSecretsClient
   import os
   os.environ["SLM_API_KEY"] = UserSecretsClient().get_secret("SLM_API_KEY")
   !python /kaggle/input/datasets/<user>/<dataset>/slm_host.py     # the path printed by the find command
   ```

4. Wait about 5-10 minutes. Most of that time is the first download of the three models (about 19 GB). The cell prints:

   ```
   GPU: Tesla T4, 15360 MiB; Tesla T4, 15360 MiB
   qwen2.5-coder:14b: loaded and answering JSON (25.3s)
   ...
   SLM host is ready. Put these two lines in SpecBridge's .env (BRAIN=slm):
   SLM_BASE_URL=https://<random>.trycloudflare.com/v1
   ```

5. **Leave the cell running and the tab open.** The host restarts Ollama or the tunnel if either stops. A new tunnel has a new address, and it is printed in the same cell.

## 3. Point SpecBridge at it (laptop)

In `.env`:

```
BRAIN=slm
SLM_BASE_URL=https://<random>.trycloudflare.com/v1
SLM_API_KEY=<the same secret>
```

Check, then run:

```bash
.venv/bin/python scripts/run_ticket.py SPEC-1 --mode dry-run     # the brain check at START lists the host's models first
```

To go back to Gemini, set `BRAIN=llm`. The `SLM_*` lines can stay.

The Jira button (`scripts/serve.py`, [DEPLOY_JIRA.md](DEPLOY_JIRA.md)) uses the same `.env`, so it runs on the SLM too. Its "generating" comment then says 5-15 minutes instead of 2-5.

## What to expect

| | Gemini (`llm`) | SLM host (`slm`) |
|---|---|---|
| Time per ticket | 2-5 min | about 5-15 min (SPEC-1: about 6 min with 2 workers plus a retry round, 2026-11-18) |
| Cost | estimated at list price | none reported (`cost_usd` empty); the GPU is free |
| Time cap before a retry round | 600 s | 3,600 s (`config/agent.json`) |
| Worker conversation / evidence for write_cases | 15,000 tokens / 48,000 characters | 12,000 / 32,000 (`config/brains.json`) |

## Troubleshooting

| You see | Do this |
|---|---|
| `cannot reach the SLM host at ...; is the Kaggle notebook running, and is SLM_BASE_URL ...` | Check that the cell is still running. Copy the last address it printed into `.env`. |
| `the SLM host refused SLM_API_KEY` | The laptop's key and the Kaggle secret differ. Make them the same and restart the cell. |
| `the SLM host has not pulled it` | `BRAIN_MODEL` or `brains.json` names a model the host does not serve. Add it to `--models` and restart. |
| `the SLM host returned 413 ... does not fit the ... context` | The prompt is too long for that model. Lower `evidence_chars` / `worker_context_cap`, or raise that model's context in `--models`. |
| `no answer from the SLM host within 1800 s` | The host is overloaded or stuck. Look at the cell's job lines; restart the cell if Ollama hangs. |
| `no NVIDIA GPU found` in the cell | Turn on Accelerator → GPU T4 x2 and restart the session. |
| The session stopped | Kaggle sessions last up to 12 hours and stop when idle with the tab closed. Start again; the tunnel address will be new. |

The cell prints one line per answer (model, time, waiting time) and a heartbeat every 10 minutes. Logs: `~/.cache/specbridge-slm/ollama.log` and `cloudflared.log` on the Kaggle machine.

## Testing without Kaggle

On a laptop with Ollama running and a model pulled, start the host without the install and tunnel steps:

```bash
.venv/bin/python scripts/slm_host.py --no-install --no-tunnel --models "llama3.2:1b-instruct-q3_K_M=8192" --key <16+ characters>
# .env: BRAIN=slm, BRAIN_MODEL=llama3.2:1b-instruct-q3_K_M, SLM_API_KEY=<the same>; SLM_BASE_URL is not needed (127.0.0.1:8000)
```

`BRAIN_MODEL` replaces only the main model. The worker and reviewer roles keep their own models, so a test like this checks the connection and the main-model nodes. A full ticket needs all three models on the host, which is about 19 GB and too much for the laptops.

The automatic tests run a fake Ollama and need nothing: `.venv/bin/python -m pytest tests/test_slm_host.py`.

## Security

- **What is exposed:** the tunnel reaches only the key-checking server. Every endpoint except `/health` needs the key, and it is compared in constant time. Only the configured models can be used.
- **What leaves the laptop:** prompts (ticket text and code excerpts) go to the Kaggle machine, just as they go to Google with Gemini. Secrets are already removed from ticket text before any prompt (D3).
- **What is printed:** the key is printed only if the host made it up because none was given. A key from Kaggle Secrets is never printed.
- **After use:** stop the session. A quick-tunnel address dies with it.

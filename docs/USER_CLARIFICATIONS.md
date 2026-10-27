# User clarifications

Questions asked during SpecBridge planning and what the user decided. Keep this updated as new answers come in.

## Answered

| Date | Question | Answer |
|---|---|---|
| 2026-10-26 | Which React repos should SpecBridge be tested on? | OpenMRS 3 (O3) frontend repos. Chosen: `core`, `patient-chart`, `patient-management`, `billing-app`, `dispensing-app` (see `config/repos.json`). |
| 2026-10-26 | Where do the test tickets come from? | Real tickets from the public OpenMRS Jira project **O3**. |
| 2026-10-26 | How should the work be run? | One step at a time. After each step: report blockers, run a smoke test, and wait for the user to say "proceed". |
| 2026-10-26 | May the SpecBridge folder become its own git project? | Done - the user ran `git init` in SpecBridge. |
| 2026-10-26 | Who picks the final 30-50 golden tickets and writes the answers? | The team, by hand. |
| 2026-10-26 | Where to keep the downloaded repo copies? (Desktop is inside OneDrive, so the project folder syncs) | `C:\specbridge-work`, outside OneDrive. Project files stay in SpecBridge. |
| 2026-10-26 | Should this tracking file be kept up to date in later steps? | Yes. |
| 2026-10-26 | Should the "brain" be switchable between big cloud models (LLM) and small local models (SLM)? | Yes, required. The project is shared by two courses: one needs an LLM brain, the other an SLM brain. The whole product must work fully either way; only the brain changes (plan section E2, Model Adapter Layer). |
| 2026-10-26 | Jira project key and Confluence space key? | `SPEC` (project "SpecBridge Golden") and `UAT` (space "SpecBridge UAT") on `rooks101.atlassian.net`. 63 tickets copied as SPEC-1..SPEC-63. |
| 2026-10-26 | 18 golden tickets name code files. Keep, rewrite, or drop? | Keep as written and score them separately (label `mentions-files`). |
| 2026-10-26 | Which brain for now, and how to switch? | LLM through an API is the default and the only one used for now. Keep it easy to add an SLM later (one setting, `BRAIN=llm` / `BRAIN=slm`). |
| 2026-10-26 | Which cloud provider and model? | OpenRouter, using Claude models for now; must be easy to switch to other models on OpenRouter. |
| 2026-10-27 | Switch the default cloud model to Gemini? | Yes - default is now `google/gemini-3.8-flash` (through OpenRouter); `google/gemini-4-argon` for the hardest tickets. Re-check both on the golden set later. |
| 2026-10-26 | Code search / embeddings: local or cloud? | Local for now. |
| 2026-10-26 | Which small model (laptop: 15.4 GB RAM, no NVIDIA card)? | Not now - decide when the SLM course needs it. |
| 2026-10-26 | Keep one document listing all build steps (done and planned)? | Yes - `docs/BUILD_STEPS.md`, kept updated after every step. |
| 2026-10-27 | Where to keep the repo copies on the Linux laptop? | "Clone here": `/home/qasim/Documents/sem3/AutoSE/Project/specbridge-work`, beside the SpecBridge folder, not inside it. Set `SPECBRIDGE_WORKDIR` in `.env` to this path. The user asked for "4 repos", but the README lists 5, so all 5 were cloned. |
| 2026-10-27 | Which vector DB? | **SQLite + numpy** (user chose the first option). One SQLite file holds the code pieces, their labels and links, a full-text keyword index (FTS5) and the vectors; `numpy` compares a question with every vector (exact search, milliseconds at this size). No server. Reasons, measured on the 5 repos: about 5-10k pieces; many links that need joins (922 imports from `core`'s framework, 330 widgets/pages/forms in `routes.json`); 2,768 on-screen English strings that need real keyword search. The store sits behind one small interface so it can be swapped later. |
| 2026-10-27 | Step 4: stay standard-library only, or allow extra packages? | `numpy` is allowed (part of the chosen SQLite + numpy store; first needed in Step 4c). Any other package (e.g. tree-sitter) only if the scores show a need, and asked first. |
| 2026-10-27 | How far to go in one run? | "Complete all the steps": all of Step 4 (4b, 4c, 4d) done in one go, then stop before Step 5. |
| 2026-10-27 | Which local embedding model? | `nomic-embed-text` through Ollama (the recommendation, taken as part of "complete all the steps"). It reads up to 2,048 tokens (not 8k as first said); pieces are capped at about 1,500 tokens. A code-specific model can still be compared in Step 10. |
| 2026-10-27 | Ollama on the Linux laptop is broken (no model engine in `/usr/local/lib/ollama`). Reinstall, use a Python embedding library, or skip meaning search? | Reinstall Ollama (`curl -fsSL https://ollama.com/install.sh | sh`, needs sudo; the user runs it). Also fixes the SLM brain for later. |
| 2026-10-27 | `SPECBRIDGE_HANDOFF.md` (new build spec) conflicts with Steps 1-4 already built. Which wins? | **Merge into existing.** Keep the OpenMRS repos, code library and golden candidates; add the handoff's scaffold (uv, `models.py`, `llm.py`, Typer CLI, eval layout) around them. Deviations are listed in [HANDOFF_DEVIATIONS.md](HANDOFF_DEVIATIONS.md). |
| 2026-10-27 | Target repo and pinned commit (handoff §3)? | **OpenMRS, all 5 repos** at the existing pinned commits (`data/snapshots.json`). This goes against the handoff's "one repo, no multi-repo" rule on purpose. Phase 1 waits for the user's go-ahead. |
| 2026-10-27 | Agent and judge models (handoff §3)? | Agent: `openrouter/google/gemini-3.8-flash`. Judge: `openrouter/anthropic/claude-sonnet-5.5` (a different model family). Both through OpenRouter, set in `config/config.yaml`. |
| 2026-10-27 | Embedding model (handoff §3)? | `nomic-embed-text` through local Ollama (unchanged from Step 4c). |

## Still open

| Asked | Question | Recommended |
|---|---|---|
| 2026-10-26 | Scope: SpecBridge (UAT test cases) first, full autonomous-coding plan, or SpecBridge only? | SpecBridge first; code-writing as optional later |
| 2026-10-26 | Deadline (final class date) and how many teammates are building? | - |
| 2026-10-26 | Budget for OpenRouter? (Default Gemini 3.8 Flash: ~$0.04 per ticket, ~$7 for 3 rounds of 63 tickets - estimate) | Set a spending limit on the OpenRouter key |
| 2026-10-26 | Mixed mode later (small model first, hand hard parts to the big one)? | Optional, only if a course asks |
| 2026-10-26 | Trigger: automatic when a ticket is created, or a simple page/button for the prototype? | Simple page/button for the prototype |
| 2026-10-26 | Build both code-reading approaches (code library and live GitHub) and compare them? | Yes, as the proposal promises |
| 2026-10-27 | Have the LLM write a one-line "what the user sees" summary for each piece of code before indexing? (one-time cost; the SLM course would need to reuse the same summaries) | Not at first. Add it only if search scores are too low without it |
| 2026-10-27 | Pass bar for Step 4 search, measured on the golden tickets' really-changed files? | At least one changed file in the top 10 results for 80% of tickets, and per-file recall@20 reported for each group (cross-repo, vague, `mentions-files` scored separately) |

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

## Still open

| Asked | Question | Recommended |
|---|---|---|
| 2026-10-26 | Scope: SpecBridge (UAT test cases) first, full autonomous-coding plan, or SpecBridge only? | SpecBridge first; code-writing as optional later |
| 2026-10-26 | Deadline (final class date) and how many teammates are building? | - |
| 2026-10-26 | Budget for OpenRouter? (Default Gemini 3.8 Flash: ~$0.04 per ticket, ~$7 for 3 rounds of 63 tickets - estimate) | Set a spending limit on the OpenRouter key |
| 2026-10-26 | Mixed mode later (small model first, hand hard parts to the big one)? | Optional, only if a course asks |
| 2026-10-26 | Trigger: automatic when a ticket is created, or a simple page/button for the prototype? | Simple page/button for the prototype |
| 2026-10-26 | Build both code-reading approaches (code library and live GitHub) and compare them? | Yes, as the proposal promises |

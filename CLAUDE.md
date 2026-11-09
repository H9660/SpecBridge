# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SpecBridge: a PM's Jira ticket goes in; SpecBridge reads the real code of five OpenMRS 3 frontend repos and writes UAT test cases (steps and expected results) to a Confluence page. It is a two-course capstone: the whole product must work with a cloud LLM brain and, later, a local SLM brain, with only the brain changing.

Read these before changing anything substantial:
- [docs/BUILD_STEPS.md](docs/BUILD_STEPS.md): build order and status of each step.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): the agent design and decisions D1–D19, drawn in [docs/architecture.drawio](docs/architecture.drawio).
- [docs/USER_CLARIFICATIONS.md](docs/USER_CLARIFICATIONS.md): decisions the user made, plus open questions.
- [docs/repo_map.md](docs/repo_map.md): what every file does.

## Working rules for this repo

- **One step at a time.** After each step: report blockers, run its smoke test, and wait for the user to say "proceed" before starting the next. For the LangGraph agent, the user approves each node's spec (behaviour, edge cases, tests) before any code is written.
- **Keep the docs in sync in the same piece of work:**
  - [BUILD_STEPS.md](docs/BUILD_STEPS.md) as steps finish.
  - [USER_CLARIFICATIONS.md](docs/USER_CLARIFICATIONS.md) when a decision is made or a question is opened.
  - [repo_map.md](docs/repo_map.md) when a file is added or gains functionality. `scripts/check_repo_map.py` lists files missing from it.
- **Git:** work and commit directly on `main`. Don't create or switch branches unless asked, and commit only when asked.
- **Dependencies:** standard library first. Allowed packages are pinned in [requirements.txt](requirements.txt): `numpy`, `langgraph`, `langgraph-checkpoint-sqlite`, `pytest`. Ask before adding any other.
- **Docs style:** plain language, short sentences, tables.

## Environment and commands

- **Python 3.12.** Use the project venv: `.venv/bin/python` on Linux, or `.venv\Scripts\python` / `py -3.12` on Windows.
  - Install: `.venv/bin/python -m pip install -r requirements.txt`
- **Settings:** come from `.env` (copy `.env.example`), read by `specbridge/env.py`. Real environment variables starting `BRAIN*`, `GEMINI_*` or `EMBED_*` override the file.
- **The repos SpecBridge reads** live outside this project, at `SPECBRIDGE_WORKDIR`:
  - Linux: `/home/qasim/Documents/sem3/AutoSE/Project/specbridge-work`
  - Windows: `C:/specbridge-work`
  - Each repo is checked out on a `snapshot` branch at the frozen commit in `data/snapshots.json`. Never change those checkouts: the golden-ticket answer key depends on that exact "before" state.
- **The code index** `specbridge_index.sqlite` sits in that same workdir, not in this repo. It holds keyword tables, links and vectors, and is rebuilt only when a frozen commit changes.

```
.venv/bin/python scripts/smoke_test_step4.py --workdir <workdir>          # one smoke test per step: smoke_test_step1..4; writes data/smoke_test_stepN.md
.venv/bin/python scripts/eval_retrieval.py --method hybrid --workdir <workdir>   # score code search on golden tickets (keyword|pieces|combined|vector|hybrid); writes data/retrieval/<method>.md
.venv/bin/python -m pytest tests/agent                                     # agent tests
.venv/bin/python -m pytest tests/agent/test_intake.py::test_name           # one test
```

- **Smoke-test results:** `FAIL` must not appear; `WARN` lines are explained in the report; `PENDING` means a `.env` setting is missing.
- **Embeddings (`vector` and `hybrid` methods):** need local Ollama with `nomic-embed-text` running at `127.0.0.1:11434` (settings in `config/embedder.json`). Embedding all pieces is resumable and takes tens of minutes on CPU.

## Architecture: the big picture

**1. The brain (`specbridge/brain.py`)**
- The only way to call a model. Get one with `load_brain()`, then use `ask()` or `ask_json(prompt, schema)`.
- Profiles are in `config/brains.json`. `BRAIN=llm` is Gemini called directly at Google's OpenAI-compatible endpoint with `GEMINI_API_KEY` (default `gemini-3.8-flash`; OpenRouter was dropped on 2026-11-09). Google does not report cost, so `Reply.cost_usd` is estimated from `price_usd_per_mtok` (`cost_estimated=True`), `BRAIN=slm` is Ollama, and `BRAIN_MODEL` overrides the model.
- `ask_json` validates against a JSON schema and retries once, retries busy servers, and records tokens, cost and time per answer.
- Gemini thinks before it answers, and the thinking counts against `max_tokens`, so give every call hundreds of tokens of headroom.

**2. The code library (Step 4, done)**
- Pipeline: `code_parse.py` → `code_index.py` → SQLite, with `embedder.py` adding vectors.
- **Pieces:** files are split into top-level pieces (components, hooks, functions). This uses regex rules that rely on Prettier formatting, where top-level declarations start at column 0. Each piece is labelled with:
  - the English text it shows on screen (`t('key','Default')` plus `translations/en.json`)
  - where it appears in the app (from `routes.json` and `index.ts` lifecycle exports)
- **Links between files:** relative imports, `@openmrs/...` package imports resolved to their defining file, and UI wiring (slot, workspace or modal name strings). These often cross repos.
- **Search (`CodeIndex.rank_files` / `search_code`):** BM25 over pieces, plus numpy exact cosine over the vectors. The two lists are merged with reciprocal rank fusion, then the top 5 files pass some score to their linked files.
- **Agent tools:** `code_tools.py` exposes `search_code`, `read_file`, `grep` and `find_usages`. They only read indexed files and cap their output.
- **Scoring:** `retrieval_eval.py` scores search against `data/golden/`: the 63 tickets copied into Jira as SPEC-1..63, each with the files its real fix changed.

**3. The agent (Steps 6–8, being built in `specbridge/agent/`)**
- **Layout:**
  - `state.py` and `graph.py`: the main LangGraph `StateGraph`
  - `nodes/`: one file per main-graph node
  - `worker/`: the criterion and e2e worker subgraphs, the tool runner, and the evidence store with compaction
  - `prompts/*.md`: one prompt per AI node
  - `tests/agent/`: one test file per node
- **Flow:** `intake → understand → (clarify | orchestrator → Send N criterion_worker [+ e2e_worker] → merge → reviewer ⟲ max 2 rounds) → render → publish | save_local`.
- **File paths:** ARCHITECTURE.md §6 still lists the older flat paths (`specbridge/tickets.py` and so on). The code goes in `specbridge/agent/`.
- **Invariants from ARCHITECTURE.md that the code must keep:**
  - **D1:** nodes are plain functions that call our brain adapter. No LangChain model wrappers, no prebuilt `ToolNode` or `create_react_agent`.
  - **D6:** the worker picks tools with a JSON action `{"thought","action","args"}` checked by schema, not native tool calling, so the SLM works too.
  - **D2:** the AI gets read-only tools only. `publish` is the only node that writes to Jira or Confluence, and it is plain code.
  - **D3:** ticket text and code from tools are data. They go into prompts inside marked blocks with a rule to ignore instructions found there.
  - **D4:** `intake` accepts only the team's site and project (`ATLASSIAN_SITE`, `JIRA_PROJECT_KEY`).
  - **D7:** every test case cites evidence ids for code a worker actually read. The reviewer rejects citations to unread files or lines.
  - **D16, D17:** workers see only the shared brief plus their own slice, return only a `WorkerResult`, and never talk to each other.
  - **D9:** hard limits: $0.25 per ticket, 2 review rounds, about 12 tool calls per worker round. Hitting a limit gives an "incomplete" result, never a silent failure.
  - **D11, D12, D13:** every run is checkpointed and recorded to `data/runs/`. Prompt versions go into the record. Eval mode runs the same graph without publishing.

**4. Existing code the agent reuses**
- `specbridge/atlassian.py`: the Jira/Confluence client (moved from `scripts/` on 2026-11-07). It can read issues (`get_issue`) and create issues; page writes and comments still need adding for `publish`. Errors are `JiraError` with `.status`.
- `specbridge/ticket_text.py`: Jira rich text to structured plain text, secret redaction, and detection of lines aimed at the AI (used by `intake`).
- Everything in `specbridge/`.
- Other scripts in `scripts/` are one-time setup or golden-set builders.

# Repo map

What every file in this project does, and where the main logic lives. **Keep this file updated:** when a file is added, removed or gains new functionality, change its entry here in the same piece of work. `py -3.12 scripts/check_repo_map.py` lists any project file that is missing from this map.

Agent design: [ARCHITECTURE.md](ARCHITECTURE.md). Build order and status: [BUILD_STEPS.md](BUILD_STEPS.md). Decisions: [USER_CLARIFICATIONS.md](USER_CLARIFICATIONS.md). Setup: [README.md](../README.md).

## How the pieces fit together

```
config/repos.json + data/snapshots.json      which 5 OpenMRS repos, frozen at which commit
        |  scripts/setup_workspace.py        downloads them to C:\specbridge-work
        v
specbridge/code_parse.py  -> specbridge/code_index.py  ->  specbridge_index.sqlite (outside the project)
 (split files into pieces,    (store files, pieces, links,      ^
  find on-screen text,         keyword index; search)           |  specbridge/embedder.py
  find where files appear)                                      |  (meaning vectors, local Ollama)
        |
        v
specbridge/code_tools.py   tools the AI will call: search_code, read_file, grep, find_usages
specbridge/brain.py        the AI itself (Gemini called directly at Google, or local SLM via Ollama)

Golden tickets (answer key):
scripts/build_ticket_shortlist.py -> data/golden/candidates_v0.json (files each real fix changed)
scripts/import_tickets.py         -> team Jira SPEC-1..63 + data/golden/jira_import_preview.json (cleaned text)
specbridge/retrieval_eval.py      scores search against the answer key
```

## `specbridge/` - the product code

| File | Step | What it does | Main parts |
|---|---|---|---|
| [`__init__.py`](../specbridge/__init__.py) | - | Marks the folder as a Python package. Empty. | - |
| [`env.py`](../specbridge/env.py) | 3 | Reads settings from `.env`; real environment variables (`BRAIN*`, `GEMINI_*`, `EMBED_*` and any key already in `.env`) win over the file. | `load_env()` |
| [`brain.py`](../specbridge/brain.py) | 3 | The swappable AI "brain". One interface for cloud LLMs (Gemini at Google's OpenAI-compatible endpoint; any OpenAI-style server works) and local SLMs (Ollama); estimates cost from list prices when the provider reports none and counts hidden thinking tokens; which one comes from `config/brains.json` and `BRAIN` / `BRAIN_MODEL`. Checks JSON answers against a schema and asks once more if invalid; retries busy servers patiently (`http_retries` per brain, waits 2-30 s, follows the server's Retry-After); raises a clear error if a thinking model runs out of tokens; records tokens, cost, time and `byok` (whether OpenRouter used the team's own Gemini key) per answer. | `load_brain()` [L140](../specbridge/brain.py#L140), `OpenAIChatBrain.ask()` [L88](../specbridge/brain.py#L88), `.ask_json()` [L92](../specbridge/brain.py#L92), `.model_available()`, `Reply`, `schema_errors()` |
| [`code_parse.py`](../specbridge/code_parse.py) | 4b, 4d | Reads OpenMRS frontend code without a TypeScript parser: splits a file into pieces (components, hooks, functions...), finds the English text a piece shows on screen, reads imports, and reads `routes.json` / `index.ts` to learn where a file appears in the app (widget, page, workspace, modal). | `split_pieces()` [L44](../specbridge/code_parse.py#L44), `screen_text()` [L81](../specbridge/code_parse.py#L81), `imports()`, `resolve()`, `routes_entries()` [L130](../specbridge/code_parse.py#L130), `lifecycle_files()`, `ui_names()` |
| [`code_index.py`](../specbridge/code_index.py) | 4a-4d | The code library. Builds one SQLite file next to the repos (files, pieces, links between files, keyword index, meaning vectors), rebuilt only when a repo's frozen commit changes. All search lives here. | `CodeIndex.build()` [L129](../specbridge/code_index.py#L129), `.search()` (whole files) [L316](../specbridge/code_index.py#L316), `.search_pieces()` (keywords) [L327](../specbridge/code_index.py#L327), `.build_vectors()` [L358](../specbridge/code_index.py#L358), `.search_vectors()` (meaning) [L386](../specbridge/code_index.py#L386), `.follow_links()` [L408](../specbridge/code_index.py#L408), `.rank_files()` (combined / hybrid) [L419](../specbridge/code_index.py#L419), `.search_code()` (for the AI) [L428](../specbridge/code_index.py#L428), `.neighbours()`, `.find_screen()` (is a screen name in the code?), `.screens_for()` (registered screens most related to a text; both used by understand, D20), `rrf()` [L459](../specbridge/code_index.py#L459), `words()`, `query_terms()` |
| [`embedder.py`](../specbridge/embedder.py) | 4c | Turns text into meaning vectors through local Ollama (`nomic-embed-text` by default, `EMBED_MODEL` to override), with the document / question prefixes nomic expects. | `load_embedder()`, `OllamaEmbedder.embed_documents()`, `.embed_query()` |
| [`code_tools.py`](../specbridge/code_tools.py) | 4d | The tools the AI calls to read code, with their JSON schemas (`TOOLS`). Only files in the library can be read. | `CodeTools.call()`, `.search_code()`, `.read_file()`, `.grep()`, `.find_usages()` |
| [`atlassian.py`](../specbridge/atlassian.py) | 2, node 1 | Small client for the team's Jira + Confluence: login check, read one issue (`get_issue`), issue types, Confluence space, search, create issue. Errors are `JiraError` with the HTTP status and never contain the credentials. Moved here from `scripts/` on 2026-11-07. | `Atlassian`, `.get_issue()`, `.search()`, `JiraError`, `missing_settings()` |
| [`ticket_text.py`](../specbridge/ticket_text.py) | node 1 | Jira ticket to clean, safe text: rich text to plain text keeping headings, lists (one criterion per line), code blocks and tables; secrets to `<redacted-secret>` (only values that look like secrets, so "password field" stays); finds lines aimed at the AI. | `adf_to_text()`, `redact_secrets()`, `instruction_lines()`, `file_names()` |
| [`retrieval_eval.py`](../specbridge/retrieval_eval.py) | 4a | Scores code search on the golden tickets: does each ticket's really-changed file come back near the top? Produces hit@k, recall@k and mrr, overall, per group and with / without file names in the ticket. | `golden_queries()` (ticket text + answer-key files) [L37](../specbridge/retrieval_eval.py#L37), `score()` [L59](../specbridge/retrieval_eval.py#L59), `summarise()` [L77](../specbridge/retrieval_eval.py#L77), `report_md()` |

## `specbridge/agent/` - the LangGraph agent (built node by node, in the order of architecture.drawio)

Node order: START (node 0), intake (1), understand (2), clarify (3), orchestrator (4), criterion_worker (5), e2e_worker (6), merge (7), reviewer (8), render (9), save_local (10), publish (11). Each node's file stays empty until its node is built, and its spec is approved first.

| File | Node | What it does | Main parts |
|---|---|---|---|
| [`graph.py`](../specbridge/agent/graph.py) | 0 | The main graph (now START -> intake -> understand -> clarify when test scope is `none`, else END until the orchestrator exists) and START itself: checks the request (ticket reference, mode - `live` refused until publish exists - run id), loads settings, runs the brain check, creates the run, runs the graph with a SQLite checkpointer (resume after a pause, crash or Ctrl-C), writes the run record however the run ends. | `run_ticket()`, `build_graph()`, `RunResult`, `StartError` |
| [`state.py`](../specbridge/agent/state.py) | 0 | `SpecBridgeState`: fields set by START and the nodes built so far; `trace` is appended and `spent` summed across nodes. | `SpecBridgeState`, `MODES`, `ENABLED_MODES`, `add_spent()` |
| [`limits.py`](../specbridge/agent/limits.py) | 0 | Reads and checks `config/agent.json` (defaults if missing; clear error for broken JSON, wrong types, unknown names). | `load_settings()`, `Settings`, `SettingsError` |
| [`preflight.py`](../specbridge/agent/preflight.py) | 0 | Brain check at START: the profile and key exist (offline); one free call lists the provider's models, which proves the key works (Google answers a bad key with HTTP 400) and that the model is offered. No question is sent to the model. Never shows the key. | `check_brain()`, `PreflightError` |
| [`run_record.py`](../specbridge/agent/run_record.py) | 0 | Writes `data/runs/<ticket>/<run_id>.json`: status, error, trace, timings, spending, brain, settings, frozen commits. No keys. | `write()`, `path_for()` |
| [`nodes/intake.py`](../specbridge/agent/nodes/intake.py) | 1 | Reads the ticket reference (URL, board link or key), refuses anything outside `ATLASSIAN_SITE` / project `SPEC` before any call, fetches the ticket read-only (one retry), cleans it, redacts secrets, flags lines aimed at the AI. Out: `state["ticket"]`. | `make_node()`, `parse_ref()`, `fetch()`, `clean_issue()`, `IntakeError` |
| [`nodes/understand.py`](../specbridge/agent/nodes/understand.py) | 2 | One AI call (`ask_json`, fixed schema, prompt `prompts/understand.md`, ticket in a `<ticket>` data block, short product description) -> intent, criteria, screens, roles, questions, risks, domain fit. Then code checks: a stated criterion must quote the ticket (else inferred), ids renumbered, intake flags become risks, every screen looked up in the code library, domain fit, final testable decision and test scope (full / regression / none, D21) by rules, answer redacted again. Out: `state["understanding"]`. | `make_node()`, `finish()`, `decide()`, `check_criteria()`, `check_screens()`, `SCHEMA`, `UnderstandError` |
| [`nodes/clarify.py`](../specbridge/agent/nodes/clarify.py) | 3 | Code only. For a ticket with test scope `none`: picks the category (off-domain, backend-only, missing-screen, no-criteria, ai-judgement), headline, reason, what was understood, the PM's questions (understand's, de-duplicated, or a fixed one per category; any that read like instructions to an AI are dropped), the next step, and a plain-text Jira comment with the top 5 questions, a `[SpecBridge]` marker and a `{page_url}` placeholder for publish. Secrets redacted. Sets status `needs-clarification`. | `node()`, `category_of()`, `questions_for()`, `build_comment()`, `scope_of()` |
| `nodes/orchestrator.py`, `merge.py`, `reviewer.py`, `render.py`, `save_local.py`, `publish.py` | 4-11 | Empty until their node is built. | - |
| `worker/criterion_worker.py`, `e2e_worker.py`, `tools.py`, `evidence.py` | 5-6 | Empty until the worker nodes are built (subgraph, tool runner, evidence store and compaction). | - |
| `code_source.py` | 5 | Empty: the code-reading interface around `code_tools.py` (ARCHITECTURE.md D5). | - |

## `prompts/` - one prompt per AI node (D12)

[`understand.md`](../prompts/understand.md) (node 2): the analyst instructions; first line is `version: understand-vN (date)`, saved with every answer. `worker_agent.md`, `write_cases.md`, `e2e.md`, `merge_editor.md`, `reviewer.md`: empty until their node is built.

## `tests/` - other tests

| File | What it checks |
|---|---|
| [`test_brain.py`](../tests/test_brain.py) | The brain's token counting (hidden thinking included) and cost: list-price estimate when the provider sends none, reported cost otherwise; the default brain is Gemini at Google. |

## `tests/agent/` - tests for each agent node

Run with `.venv/bin/python -m pytest tests/agent` (one test: `... tests/agent/test_start.py::test_good_run_creates_state_trace_and_record`). Tests marked `live` need keys in `.env` and are skipped without them.

| File | Node | What it checks |
|---|---|---|
| [`conftest.py`](../tests/agent/conftest.py) | - | Shared fixtures: temp records folder, fake brain check, fake Jira (`FakeJira`, answers from the saved tickets), `start()` helper. |
| [`test_intake.py`](../tests/agent/test_intake.py) | 1 | Accepted and refused references (no network call when refused), fetch errors and retry, every rich-text element, secrets redacted / normal text untouched, AI-aimed lines found / normal lines not, the saved real tickets, other flags, intake inside the graph, live: all 69 tickets and the fixtures still matching Jira. |
| [`fixtures/jira/`](../tests/agent/fixtures/jira/) | 1 | 8 real SPEC tickets as Jira returns them (`SPEC-1.json`, `SPEC-6.json`, `SPEC-16.json`, `SPEC-55.json`, `SPEC-63.json`, `SPEC-65.json`, `SPEC-66.json`, `SPEC-69.json`), chosen to cover every rich-text element seen plus the secret, injection and Hinglish tickets. |
| [`test_start.py`](../tests/agent/test_start.py) | 0 | Normal run, every refused request, settings checks, brain check refusals (key never shown), crash / Ctrl-C / pause and resume, duplicate run id, command line, live brain check. |
| [`test_clarify.py`](../tests/agent/test_clarify.py) | 3 | Category order, fixed questions, de-duplication, dropping injected questions, redaction, the Jira comment (marker, top 5, cap, placeholder), real saved answers (SPEC-35, SPEC-3), wrong routing, and the graph branch (not testable -> clarify; testable / regression -> stop with a note; pause and resume). |
| [`fixtures/understand/`](../tests/agent/fixtures/understand/) | 3 | Two real understand answers saved from live runs (`SPEC-35.json` no criteria, `SPEC-3.json` backend-only under v2), used as clarify's inputs. |
| [`test_understand.py`](../tests/agent/test_understand.py) | 2 | Prompt (data block, flags, product, no secret), schema, every code check (quotes, ids, flag risks, screens, domain fit, testable rules, redaction), AI errors and resume, in the graph; live: the 6 trick tickets and the 4 off-domain tickets. |
`test_orchestrator.py`, `test_criterion_worker.py`, `test_e2e_worker.py`, `test_merge.py`, `test_reviewer.py`, `test_render.py`, `test_save_local.py`, `test_publish.py`, `test_graph.py`, `test_state.py` | 1-11 | Empty until their node is built. |

## `scripts/` - commands you run

| File | Step | What it does | Run with |
|---|---|---|---|
| [`build_ticket_shortlist.py`](../scripts/build_ticket_shortlist.py) | 1 | Finds O3 tickets fixed after the 31 March 2026 cutoff from the repos' git history, records the files each fix changed (the answer key), drops unusable tickets, tags the rest, and writes the frozen commits. | `py -3.12 scripts/build_ticket_shortlist.py` |
| [`render_shortlist.py`](../scripts/render_shortlist.py) | 1 | Turns `picked_v0.json` into the readable `shortlist_v0.md`. | `py -3.12 scripts/render_shortlist.py` |
| [`setup_workspace.py`](../scripts/setup_workspace.py) | 2 | Downloads the 5 repos and puts each on a `snapshot` branch at its frozen commit. Safe to re-run. | `py -3.12 scripts/setup_workspace.py --workdir C:/specbridge-work` |
| [`import_tickets.py`](../scripts/import_tickets.py) | 2 | Copies the 63 picked tickets into Jira project `SPEC`, removing anything that gives away the answer (PR links, links back to OpenMRS, attachments, mentions); flags tickets that name code files. Re-runs make no duplicates. | `py -3.12 scripts/import_tickets.py [--dry-run]` |
| [`import_adversarial.py`](../scripts/import_adversarial.py) | 6 | Adds the 6 trick tickets from `adversarial_v0.json` to Jira (`adversarial-v0` label), as SPEC-64 to SPEC-69. Re-runs make no duplicates. | `py -3.12 scripts/import_adversarial.py [--dry-run]` |
| [`eval_understand.py`](../scripts/eval_understand.py) | node 2 | Runs understand (real AI) on SPEC-1..69 and the off-domain tickets and checks each against what is expected (real tickets testable and on-domain, trick tickets as labelled); writes `data/understand/<prompt version>.md` / `.json`. About $0.005 per ticket. | `.venv/bin/python scripts/eval_understand.py [--keys SPEC-12 ...]` |
| [`eval_retrieval.py`](../scripts/eval_retrieval.py) | 4 | Builds the code library if needed and scores one search method (`keyword`, `pieces`, `combined`, `vector`, `hybrid`) on the golden tickets. `vector` / `hybrid` embed all pieces first (once). | `py -3.12 scripts/eval_retrieval.py --method hybrid` |
| [`retrieval_details.py`](../scripts/retrieval_details.py) | 4 | Per-ticket evidence behind the scores: each ticket's changed files, their rank in combined and hybrid search, and the hybrid top 20. | `py -3.12 scripts/retrieval_details.py` |
| [`run_ticket.py`](../scripts/run_ticket.py) | 7 (node 0) | Runs the agent on one ticket: prints the brain, run id, status and record path. Exit 0 done, 1 failed, 2 refused, 130 Ctrl-C. | `.venv/bin/python scripts/run_ticket.py SPEC-12 [--mode dry-run\|eval] [--run-id ID --resume] [--no-preflight]` |
| [`check_repo_map.py`](../scripts/check_repo_map.py) | - | Lists project files that are missing from this repo map. | `py -3.12 scripts/check_repo_map.py` |
| [`smoke_test_step1.py`](../scripts/smoke_test_step1.py) | 1 | Checks the test data: frozen commits, ticket answer keys, cutoff rules. | `py -3.12 scripts/smoke_test_step1.py --workdir C:/specbridge-work` |
| [`smoke_test_step2.py`](../scripts/smoke_test_step2.py) | 2 | Checks the workspace: repos frozen and untouched, `.env` safe, ticket copier removes leaks, tickets copied into Jira. | `py -3.12 scripts/smoke_test_step2.py` |
| [`smoke_test_step3.py`](../scripts/smoke_test_step3.py) | 3 | Checks the brain against a fake model server (free) and, with `GEMINI_API_KEY`, live. | `py -3.12 scripts/smoke_test_step3.py` |
| [`smoke_test_step4.py`](../scripts/smoke_test_step4.py) | 4 | Checks the code library: indexing, pieces, links, tools, embeddings (fake and live) and the search scores. | `py -3.12 scripts/smoke_test_step4.py` |

## `config/` - settings

| File | What it holds |
|---|---|
| [`repos.json`](../config/repos.json) | The 5 OpenMRS repos (name, GitHub URL, what each contains), the cutoff date and the source Jira project. |
| [`brains.json`](../config/brains.json) | Brain profiles: `llm` (Gemini at Google, default `gemini-3.8-flash`, `GEMINI_API_KEY`, list prices for cost estimates) and `slm` (local Ollama, model not chosen yet). |
| [`embedder.json`](../config/embedder.json) | Embedding model settings: local Ollama, `nomic-embed-text`, piece size cap, batch size. |
| [`agent.json`](../config/agent.json) | Agent limits: $0.25 cost cap, 2 rounds (first run + 1 retry), 10 min time cap, 12 tool calls per worker round, 20% reserve, max 5 workers, concurrency per brain. |

## `data/` - inputs and results

| File | Made by | What it holds |
|---|---|---|
| [`snapshots.json`](../data/snapshots.json) | build_ticket_shortlist | The frozen commit (31 March 2026) of each repo. |
| [`golden/candidates_v0.json`](../data/golden/candidates_v0.json) / [`.md`](../data/golden/candidates_v0.md) | build_ticket_shortlist | All usable candidate tickets, with `changed_code_files` (the answer key) and tags. |
| [`golden/picked_v0.json`](../data/golden/picked_v0.json) | the team | The 63 hand-picked tickets and their groups (cross-repo, clear, normal, vague, security). |
| [`golden/shortlist_v0.md`](../data/golden/shortlist_v0.md) | render_shortlist | Readable list of the picked tickets. |
| [`golden/adversarial_v0.md`](../data/golden/adversarial_v0.md) / [`.json`](../data/golden/adversarial_v0.json) | hand-written (Step 6) | The 6 trick tickets (fake screen, secret in ticket, hidden instructions, contradictory criteria, backend-only, informal Hinglish) with the expected behaviour for each. In Jira as SPEC-64 to SPEC-69. |
| [`golden/adversarial_import_map.json`](../data/golden/adversarial_import_map.json) | import_adversarial | ADV-n -> SPEC-n key. |
| [`golden/off_domain_v0.json`](../data/golden/off_domain_v0.json) | hand-written (node 2) | 4 tickets for the domain-fit check, not in Jira: flight booking and a Bitcoin wallet (unrelated), a quote of the day (odd but plausible), blood group in the banner (fits). |
| [`golden/jira_import_preview.json`](../data/golden/jira_import_preview.json) | import_tickets | The cleaned ticket text (what search and the AI are given) and what was removed from each ticket. |
| [`golden/jira_import_map.json`](../data/golden/jira_import_map.json) | import_tickets | Original OpenMRS key -> copied `SPEC-n` key. |
| [`golden/smoke_test_step1.md`](../data/golden/smoke_test_step1.md), [`smoke_test_step2.md`](../data/smoke_test_step2.md), [`smoke_test_step3.md`](../data/smoke_test_step3.md), [`smoke_test_step4.md`](../data/smoke_test_step4.md) | smoke tests | Latest result of each step's smoke test. |
| [`retrieval/<method>.md`](../data/retrieval/) / `.json` | eval_retrieval | Scores for `keyword`, `pieces`, `combined`, `hybrid` search: summary table and per-ticket rows. |
| [`retrieval/details.md`](../data/retrieval/details.md) / `.json` | retrieval_details | Per ticket: changed files, their ranks, hybrid top 20. |
| [`understand/understand-v1.md`](../data/understand/) / `.json` | eval_understand | understand's answers on every SPEC ticket and off-domain ticket, scored against what is expected, with cost and time. |

## Project root and `docs/`

| File | What it is |
|---|---|
| [`README.md`](../README.md) | Setup: what you need, cloning the frozen repos, `.env`, smoke tests, brain switching. |
| [`.env.example`](../.env.example) | Template for `.env` (Atlassian, Gemini key, brain, work folder). Copy to `.env`. |
| [`.gitignore`](../.gitignore) | Keeps `.env`, caches, editor files and agent run records (`data/runs/`) out of git. |
| [`requirements.txt`](../requirements.txt) | Exact versions of the allowed packages (`numpy`, `langgraph`, `langgraph-checkpoint-sqlite`, `pytest`). Install into `.venv` with `.venv/bin/python -m pip install -r requirements.txt`. |
| [`CLAUDE.md`](../CLAUDE.md) | Guidance for Claude Code: working rules, commands, architecture overview. |
| [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) | Design of the agent that turns a ticket URL into a UAT page: a LangGraph `StateGraph` with an orchestrator and criterion-worker subagents; key decisions D1-D19, how context is divided, communication, subagent counts, state, planned files, scoring, security. |
| [`docs/architecture.drawio`](architecture.drawio) | The same architecture as a draw.io diagram: main graph (orchestrator, parallel workers, merge, reviewer loop), one worker subgraph expanded, state, context layers, services, legend. Open in draw.io / diagrams.net. |
| [`docs/SpecBridge_AI_PRD.tex`](SpecBridge_AI_PRD.tex) | The PRD as LaTeX (same content as the PDF). Standard packages only; compile with `pdflatex SpecBridge_AI_PRD.tex` (TeX Live, MiKTeX or Overleaf). |
| [`docs/SpecBridge_AI_PRD.pdf`](SpecBridge_AI_PRD.pdf) | The PRD (course deliverable 1, AI for Product Managers), A4 PDF: user and job-to-be-done, build-vs-rules case, approach, risks, success metric, proposed ship gate. Printed from the live page https://claude.ai/artifact/8TnKtUPLLDqoiMV3VxEqv1; re-print after changes to the page. |
| [`docs/golden_set_eval_rubric_v0.md`](golden_set_eval_rubric_v0.md) | Course activity 3: 10 labelled golden examples (5 happy, 3 edge, 2 adversarial) from the `SPEC` tickets, rubric v0 (coverage, groundedness, safety and honesty, with pass/partial/fail anchors), who scores what (code checks, LLM judge, 2 human raters) and how the judge is spot-checked. Labels await team sign-off. |
| [`docs/customer_plan.md`](customer_plan.md) | Course activity 4: the 5 real users (U1-U5) with roles and why each fits, outreach and session dates this week, the 30-minute session script, notes template and status tracker. |
| [`docs/PRD_TEAM07.pdf`](PRD_TEAM07.pdf) | Team 07's PRD as submitted (5 pages, with references), the team's final layout of the PRD. |
| [`docs/SpecBridge_Mid_Submission_Report.pdf`](SpecBridge_Mid_Submission_Report.pdf) | Mid-submission progress report (Automated Software Engineering project), 4 A4 pages: Phase 1 milestones (Steps 1-4) with smoke-test results and search scores, commit history, agent architecture, Phase 2 plan (Steps 6-11), risks. Exported from the live doc https://claude.ai/artifact/RVxMfkCBzY1qymgMCusdSK; re-export after changes. |
| [`CLAUDE.md`](../CLAUDE.md) | Guidance for Claude Code: commands, architecture, working rules for this repo. |
| [`docs/adr/README.md`](adr/README.md) | How decisions are recorded (D20 onward, one file each; D1-D19 stay in ARCHITECTURE.md), the list of ADRs and a template. |
| [`docs/adr/0020-ground-understand-in-registered-screens.md`](adr/0020-ground-understand-in-registered-screens.md) | D20: understand is shown the registered screens most related to the ticket (ground truth from the repos, generated at run time) and labels screens existing / new; only an existing screen missing from the code blocks a ticket. |
| [`docs/adr/0021-regression-check-for-backend-only-changes.md`](adr/0021-regression-check-for-backend-only-changes.md) | D21: each ticket gets a test scope (full / regression / none); a backend-only change to an existing screen's code gets a regression check, other untestable tickets go to clarify; future plan to re-run from understand when the PM answers in Jira. |
| [`docs/BUILD_STEPS.md`](BUILD_STEPS.md) | The 11 build steps: done, in progress, planned. |
| [`docs/USER_CLARIFICATIONS.md`](USER_CLARIFICATIONS.md) | Every question asked and the decision taken. |
| [`docs/repo_map.md`](repo_map.md) | This file. |
| [`autonomous_software_engineering_plan.md`](../autonomous_software_engineering_plan.md) | The original plan (sections E1-E12); BUILD_STEPS maps steps to it. |
| `Proposal_Unmanned_Rooks.pdf` | The team's project proposal (SpecBridge scope, two code-reading approaches, success measures). |
| `AI for PMs - The Capstone Project - IIIT Hyderabad.pdf` | The course brief (golden dataset, rubric + LLM judge, iterations, real users, deliverables). |

## Not in the project folder (generated or secret)

| Path | What it is |
|---|---|
| `.env` | Your secrets and settings. Git-ignored; never commit or share. |
| `data/runs/<ticket>/<run_id>.json`, `data/runs/checkpoints.sqlite` | Agent run records and LangGraph checkpoints (git-ignored). |
| `C:\specbridge-work\<repo>` | The 5 frozen repos (`setup_workspace.py`). |
| `C:\specbridge-work\specbridge_index.sqlite` | The code library database (`eval_retrieval.py` builds it; about 40 MB with vectors). |

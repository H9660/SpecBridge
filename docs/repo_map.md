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
specbridge/brain.py        the AI itself (cloud LLM via OpenRouter, or local SLM via Ollama)

Golden tickets (answer key):
scripts/build_ticket_shortlist.py -> data/golden/candidates_v0.json (files each real fix changed)
scripts/import_tickets.py         -> team Jira SPEC-1..63 + data/golden/jira_import_preview.json (cleaned text)
specbridge/retrieval_eval.py      scores search against the answer key
```

## `specbridge/` - the product code

| File | Step | What it does | Main parts |
|---|---|---|---|
| [`__init__.py`](../specbridge/__init__.py) | - | Marks the folder as a Python package. Empty. | - |
| [`env.py`](../specbridge/env.py) | 3 | Reads settings from `.env`; real environment variables (`BRAIN*`, `OPENROUTER_*`, `EMBED_*` and any key already in `.env`) win over the file. | `load_env()` |
| [`brain.py`](../specbridge/brain.py) | 3 | The swappable AI "brain". One interface for cloud LLMs (OpenRouter) and local SLMs (Ollama); which one comes from `config/brains.json` and `BRAIN` / `BRAIN_MODEL`. Checks JSON answers against a schema and asks once more if invalid; retries busy servers patiently (`http_retries` per brain, waits 2-30 s, follows the server's Retry-After); raises a clear error if a thinking model runs out of tokens; records tokens, cost, time and `byok` (whether OpenRouter used the team's own Gemini key) per answer. | `load_brain()` [L140](../specbridge/brain.py#L140), `OpenAIChatBrain.ask()` [L88](../specbridge/brain.py#L88), `.ask_json()` [L92](../specbridge/brain.py#L92), `.model_available()`, `Reply`, `schema_errors()` |
| [`code_parse.py`](../specbridge/code_parse.py) | 4b, 4d | Reads OpenMRS frontend code without a TypeScript parser: splits a file into pieces (components, hooks, functions...), finds the English text a piece shows on screen, reads imports, and reads `routes.json` / `index.ts` to learn where a file appears in the app (widget, page, workspace, modal). | `split_pieces()` [L44](../specbridge/code_parse.py#L44), `screen_text()` [L81](../specbridge/code_parse.py#L81), `imports()`, `resolve()`, `routes_entries()` [L130](../specbridge/code_parse.py#L130), `lifecycle_files()`, `ui_names()` |
| [`code_index.py`](../specbridge/code_index.py) | 4a-4d | The code library. Builds one SQLite file next to the repos (files, pieces, links between files, keyword index, meaning vectors), rebuilt only when a repo's frozen commit changes. All search lives here. | `CodeIndex.build()` [L129](../specbridge/code_index.py#L129), `.search()` (whole files) [L316](../specbridge/code_index.py#L316), `.search_pieces()` (keywords) [L327](../specbridge/code_index.py#L327), `.build_vectors()` [L358](../specbridge/code_index.py#L358), `.search_vectors()` (meaning) [L386](../specbridge/code_index.py#L386), `.follow_links()` [L408](../specbridge/code_index.py#L408), `.rank_files()` (combined / hybrid) [L419](../specbridge/code_index.py#L419), `.search_code()` (for the AI) [L428](../specbridge/code_index.py#L428), `.neighbours()`, `rrf()` [L459](../specbridge/code_index.py#L459), `words()`, `query_terms()` |
| [`embedder.py`](../specbridge/embedder.py) | 4c | Turns text into meaning vectors through local Ollama (`nomic-embed-text` by default, `EMBED_MODEL` to override), with the document / question prefixes nomic expects. | `load_embedder()`, `OllamaEmbedder.embed_documents()`, `.embed_query()` |
| [`code_tools.py`](../specbridge/code_tools.py) | 4d | The tools the AI calls to read code, with their JSON schemas (`TOOLS`). Only files in the library can be read. | `CodeTools.call()`, `.search_code()`, `.read_file()`, `.grep()`, `.find_usages()` |
| [`retrieval_eval.py`](../specbridge/retrieval_eval.py) | 4a | Scores code search on the golden tickets: does each ticket's really-changed file come back near the top? Produces hit@k, recall@k and mrr, overall, per group and with / without file names in the ticket. | `golden_queries()` (ticket text + answer-key files) [L37](../specbridge/retrieval_eval.py#L37), `score()` [L59](../specbridge/retrieval_eval.py#L59), `summarise()` [L77](../specbridge/retrieval_eval.py#L77), `report_md()` |

## `scripts/` - commands you run

| File | Step | What it does | Run with |
|---|---|---|---|
| [`build_ticket_shortlist.py`](../scripts/build_ticket_shortlist.py) | 1 | Finds O3 tickets fixed after the 31 March 2026 cutoff from the repos' git history, records the files each fix changed (the answer key), drops unusable tickets, tags the rest, and writes the frozen commits. | `py -3.12 scripts/build_ticket_shortlist.py` |
| [`render_shortlist.py`](../scripts/render_shortlist.py) | 1 | Turns `picked_v0.json` into the readable `shortlist_v0.md`. | `py -3.12 scripts/render_shortlist.py` |
| [`setup_workspace.py`](../scripts/setup_workspace.py) | 2 | Downloads the 5 repos and puts each on a `snapshot` branch at its frozen commit. Safe to re-run. | `py -3.12 scripts/setup_workspace.py --workdir C:/specbridge-work` |
| [`atlassian.py`](../scripts/atlassian.py) | 2 | Small client for the team's Jira + Confluence (login check, issue types, Confluence space, search, create issue). | used by other scripts |
| [`import_tickets.py`](../scripts/import_tickets.py) | 2 | Copies the 63 picked tickets into Jira project `SPEC`, removing anything that gives away the answer (PR links, links back to OpenMRS, attachments, mentions); flags tickets that name code files. Re-runs make no duplicates. | `py -3.12 scripts/import_tickets.py [--dry-run]` |
| [`import_adversarial.py`](../scripts/import_adversarial.py) | 6 | Adds the 6 trick tickets from `adversarial_v0.json` to Jira (`adversarial-v0` label), as SPEC-64 to SPEC-69. Re-runs make no duplicates. | `py -3.12 scripts/import_adversarial.py [--dry-run]` |
| [`eval_retrieval.py`](../scripts/eval_retrieval.py) | 4 | Builds the code library if needed and scores one search method (`keyword`, `pieces`, `combined`, `vector`, `hybrid`) on the golden tickets. `vector` / `hybrid` embed all pieces first (once). | `py -3.12 scripts/eval_retrieval.py --method hybrid` |
| [`retrieval_details.py`](../scripts/retrieval_details.py) | 4 | Per-ticket evidence behind the scores: each ticket's changed files, their rank in combined and hybrid search, and the hybrid top 20. | `py -3.12 scripts/retrieval_details.py` |
| [`check_repo_map.py`](../scripts/check_repo_map.py) | - | Lists project files that are missing from this repo map. | `py -3.12 scripts/check_repo_map.py` |
| [`smoke_test_step1.py`](../scripts/smoke_test_step1.py) | 1 | Checks the test data: frozen commits, ticket answer keys, cutoff rules. | `py -3.12 scripts/smoke_test_step1.py --workdir C:/specbridge-work` |
| [`smoke_test_step2.py`](../scripts/smoke_test_step2.py) | 2 | Checks the workspace: repos frozen and untouched, `.env` safe, ticket copier removes leaks, tickets copied into Jira. | `py -3.12 scripts/smoke_test_step2.py` |
| [`smoke_test_step3.py`](../scripts/smoke_test_step3.py) | 3 | Checks the brain against a fake model server (free) and, with `OPENROUTER_API_KEY`, live. | `py -3.12 scripts/smoke_test_step3.py` |
| [`smoke_test_step4.py`](../scripts/smoke_test_step4.py) | 4 | Checks the code library: indexing, pieces, links, tools, embeddings (fake and live) and the search scores. | `py -3.12 scripts/smoke_test_step4.py` |

## `config/` - settings

| File | What it holds |
|---|---|
| [`repos.json`](../config/repos.json) | The 5 OpenMRS repos (name, GitHub URL, what each contains), the cutoff date and the source Jira project. |
| [`brains.json`](../config/brains.json) | Brain profiles: `llm` (OpenRouter, default `google/gemini-3.8-flash`) and `slm` (local Ollama, model not chosen yet). |
| [`embedder.json`](../config/embedder.json) | Embedding model settings: local Ollama, `nomic-embed-text`, piece size cap, batch size. |

## `data/` - inputs and results

| File | Made by | What it holds |
|---|---|---|
| [`snapshots.json`](../data/snapshots.json) | build_ticket_shortlist | The frozen commit (31 March 2026) of each repo. |
| [`golden/candidates_v0.json`](../data/golden/candidates_v0.json) / [`.md`](../data/golden/candidates_v0.md) | build_ticket_shortlist | All usable candidate tickets, with `changed_code_files` (the answer key) and tags. |
| [`golden/picked_v0.json`](../data/golden/picked_v0.json) | the team | The 63 hand-picked tickets and their groups (cross-repo, clear, normal, vague, security). |
| [`golden/shortlist_v0.md`](../data/golden/shortlist_v0.md) | render_shortlist | Readable list of the picked tickets. |
| [`golden/adversarial_v0.md`](../data/golden/adversarial_v0.md) / [`.json`](../data/golden/adversarial_v0.json) | hand-written (Step 6) | The 6 trick tickets (fake screen, secret in ticket, hidden instructions, contradictory criteria, backend-only, informal Hinglish) with the expected behaviour for each. In Jira as SPEC-64 to SPEC-69. |
| [`golden/adversarial_import_map.json`](../data/golden/adversarial_import_map.json) | import_adversarial | ADV-n -> SPEC-n key. |
| [`golden/jira_import_preview.json`](../data/golden/jira_import_preview.json) | import_tickets | The cleaned ticket text (what search and the AI are given) and what was removed from each ticket. |
| [`golden/jira_import_map.json`](../data/golden/jira_import_map.json) | import_tickets | Original OpenMRS key -> copied `SPEC-n` key. |
| [`golden/smoke_test_step1.md`](../data/golden/smoke_test_step1.md), [`smoke_test_step2.md`](../data/smoke_test_step2.md), [`smoke_test_step3.md`](../data/smoke_test_step3.md), [`smoke_test_step4.md`](../data/smoke_test_step4.md) | smoke tests | Latest result of each step's smoke test. |
| [`retrieval/<method>.md`](../data/retrieval/) / `.json` | eval_retrieval | Scores for `keyword`, `pieces`, `combined`, `hybrid` search: summary table and per-ticket rows. |
| [`retrieval/details.md`](../data/retrieval/details.md) / `.json` | retrieval_details | Per ticket: changed files, their ranks, hybrid top 20. |

## Project root and `docs/`

| File | What it is |
|---|---|
| [`README.md`](../README.md) | Setup: what you need, cloning the frozen repos, `.env`, smoke tests, brain switching. |
| [`.env.example`](../.env.example) | Template for `.env` (Atlassian, OpenRouter key, brain, work folder). Copy to `.env`. |
| [`.gitignore`](../.gitignore) | Keeps `.env`, caches and editor files out of git. |
| [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) | Design of the agent that turns a ticket URL into a UAT page: a LangGraph `StateGraph` with an orchestrator and criterion-worker subagents; key decisions D1-D19, how context is divided, communication, subagent counts, state, planned files, scoring, security. |
| [`docs/architecture.drawio`](architecture.drawio) | The same architecture as a draw.io diagram: main graph (orchestrator, parallel workers, merge, reviewer loop), one worker subgraph expanded, state, context layers, services, legend. Open in draw.io / diagrams.net. |
| [`docs/SpecBridge_AI_PRD.tex`](SpecBridge_AI_PRD.tex) | The PRD as LaTeX (same content as the PDF). Standard packages only; compile with `pdflatex SpecBridge_AI_PRD.tex` (TeX Live, MiKTeX or Overleaf). |
| [`docs/SpecBridge_AI_PRD.pdf`](SpecBridge_AI_PRD.pdf) | The PRD (course deliverable 1, AI for Product Managers), A4 PDF: user and job-to-be-done, build-vs-rules case, approach, risks, success metric, proposed ship gate. Printed from the live page https://claude.ai/artifact/8TnKtUPLLDqoiMV3VxEqv1; re-print after changes to the page. |
| [`docs/golden_set_eval_rubric_v0.md`](golden_set_eval_rubric_v0.md) | Course activity 3: 10 labelled golden examples (5 happy, 3 edge, 2 adversarial) from the `SPEC` tickets, rubric v0 (coverage, groundedness, safety and honesty, with pass/partial/fail anchors), who scores what (code checks, LLM judge, 2 human raters) and how the judge is spot-checked. Labels await team sign-off. |
| [`docs/customer_plan.md`](customer_plan.md) | Course activity 4: the 5 real users (U1-U5) with roles and why each fits, outreach and session dates this week, the 30-minute session script, notes template and status tracker. |
| [`docs/PRD_TEAM07.pdf`](PRD_TEAM07.pdf) | Team 07's PRD as submitted (5 pages, with references), the team's final layout of the PRD. |
| [`docs/SpecBridge_Mid_Submission_Report.pdf`](SpecBridge_Mid_Submission_Report.pdf) | Mid-submission progress report (Automated Software Engineering project), 4 A4 pages: Phase 1 milestones (Steps 1-4) with smoke-test results and search scores, commit history, agent architecture, Phase 2 plan (Steps 6-11), risks. Exported from the live doc https://claude.ai/artifact/RVxMfkCBzY1qymgMCusdSK; re-export after changes. |
| [`CLAUDE.md`](../CLAUDE.md) | Guidance for Claude Code: commands, architecture, working rules for this repo. |
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
| `C:\specbridge-work\<repo>` | The 5 frozen repos (`setup_workspace.py`). |
| `C:\specbridge-work\specbridge_index.sqlite` | The code library database (`eval_retrieval.py` builds it; about 40 MB with vectors). |

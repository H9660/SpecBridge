# SpecBridge build steps

What we are building, one step at a time. After each step: report blockers, run its smoke test, and wait for "proceed" before starting the next. Keep this file updated as steps finish or the plan changes. Decisions behind the steps are in [USER_CLARIFICATIONS.md](USER_CLARIFICATIONS.md).

**Product:** a Jira ticket goes in; SpecBridge reads the real code and writes UAT test cases to Confluence. Writing code (plan sections E5 and E7) is out of scope for now.
**Brain:** cloud LLM through OpenRouter (default); local SLM can be switched in later.
**Test code:** 5 OpenMRS 3 frontend repos, frozen at 31 March 2026, in the folder set by `SPECBRIDGE_WORKDIR` (Windows: `C:\specbridge-work`; Linux laptop: `/home/qasim/Documents/sem3/AutoSE/Project/specbridge-work`).
**New to the project?** Follow [README.md](../README.md) first: it lists the original OpenMRS repo links with their frozen versions, how to clone them (one command: `py -3.12 scripts/setup_workspace.py`), and how to fill in `.env`.

Plan section = section of [autonomous_software_engineering_plan.md](../autonomous_software_engineering_plan.md).

## Status

| Step | What | Plan section | Status |
|---|---|---|---|
| 1 | Pick test repos and real tickets; shortlist golden candidates | E10 (evaluation data) | Done |
| 2 | Download frozen repos; copy 63 tickets into team Jira | E1, E11 (secrets) | Done |
| 3 | Swappable brain: one interface for LLM and SLM | E2 | Built - waiting for OpenRouter key |
| 4 | Code library: index the repos and search them locally (SQLite + numpy) | E4 | 4a, 4b, 4d done; 4c built - waiting for Ollama reinstall |
| 5 | Live GitHub code reading (second approach, to compare) | E4 / E5 | Planned |
| 6 | Ticket reader: pull out requirements; flag vague or unsafe tickets | E8-S1 | Planned |
| 7 | Test-case writer: UAT test cases grounded in the code | E6, E8 | Planned |
| 8 | Publish to Confluence and comment on the Jira ticket; simple trigger page | E9, E11, E12 | Planned |
| 9 | Golden answers and scoring: rubric, LLM judge, ship gate | E10 | Planned |
| 10 | Improve over 3+ rounds; compare LLM against SLM | E3, E10 | Planned |
| 11 | Real users (5+, not classmates), one-page PRD, demo, presentation | - | Planned |

Steps 4-11 are the current proposal and may change; each is agreed with the user before it starts.

**2026-10-27: build spec merged.** [SPECBRIDGE_HANDOFF.md](../SPECBRIDGE_HANDOFF.md) is now the source of truth for scope, schemas, the eval harness and build phases. It is merged with Steps 1-4, not a restart; the differences are in [HANDOFF_DEVIATIONS.md](HANDOFF_DEVIATIONS.md). **Handoff Phase 0 (scaffold) is done:** `uv` project (`pyproject.toml`, `uv.lock`, Python 3.12), `config/config.yaml`, `CLAUDE.md`, all §6 schemas in `specbridge/models.py`, a LiteLLM wrapper in `specbridge/llm.py`, a Typer CLI with every command stubbed (`uv run specbridge --help`), `scripts/repo_stats.py` (report: [repo_stats_openmrs.md](repo_stats_openmrs.md)) and tests (`uv run pytest`). Next is handoff Phase 1 (indexer), which waits for the user's go-ahead.

## Done

### Step 1 - Test repos and golden ticket candidates
- **Did:** chose 5 connected O3 repos; found tickets whose code changes all came after the 31 March 2026 cutoff; dropped unusable ones (268 found, 179 usable); team hand-picked 63 (cross-repo, clear, normal, vague, security) plus 6 adversarial tickets still to write by hand.
- **Files:** `config/repos.json`, `scripts/build_ticket_shortlist.py`, `scripts/render_shortlist.py`, `data/snapshots.json`, `data/golden/candidates_v0.*`, `data/golden/picked_v0.json`, `data/golden/shortlist_v0.md`
- **Smoke test:** `scripts/smoke_test_step1.py` -> `data/golden/smoke_test_step1.md` - all pass (2 warnings: O3-5742, O3-5729).

### Step 2 - Workspace and team Jira
- **Did:** downloaded the repos to `C:\specbridge-work` (outside OneDrive), each on a `snapshot` branch; set up `.gitignore` and `.env`; copied the 63 tickets into project `SPEC` (SPEC-1..63) with answer-revealing links, attachments and mentions removed; 18 tickets that name code files are labelled `mentions-files` and scored separately.
- **Files:** `scripts/setup_workspace.py`, `scripts/atlassian.py`, `scripts/import_tickets.py`, `.gitignore`, `.env.example`, `data/golden/jira_import_map.json`
- **Smoke test:** `scripts/smoke_test_step2.py` -> `data/smoke_test_step2.md` - 16/16 passed after import.
- **Fixed 2026-10-26:** `billing-app` had its `.git` folder deleted and `yarn.lock` rewritten by `yarn install`. Restored in place: history re-downloaded, files reset to the frozen version (installed packages kept; the changed `yarn.lock` saved to `C:\specbridge-work-old\billing-app\`). Step 1 and Step 2 smoke tests pass again.

### Step 3 - Swappable brain (LLM / SLM)
- **Did:** one interface (`ask`, `ask_json`) used by everything else; brain chosen in `config/brains.json` with `BRAIN=llm|slm`; any OpenRouter model via `BRAIN_MODEL`; JSON answers checked and retried once; every answer records brain, model, tokens, cost and time.
- **Files:** `specbridge/brain.py`, `specbridge/env.py`, `config/brains.json`
- **Smoke test:** `scripts/smoke_test_step3.py` -> `data/smoke_test_step3.md` - 12 pass, 2 pending (live OpenRouter calls need `OPENROUTER_API_KEY`), 1 skipped (SLM not chosen yet).

### Step 4a - Scoring and keyword baseline
- **Did:** chose the store: one SQLite file plus `numpy` (see USER_CLARIFICATIONS.md, 2026-10-27). Built the code library (`CodeIndex`): every code file of the 5 frozen repos (2,322 files, 1,755 non-test) in `specbridge_index.sqlite` next to the repos, with a keyword index (FTS5, BM25; code names split into words, words stemmed). Rebuilds only when a repo's commit changes (under 1 s). Built the scoring: each golden ticket's cleaned Jira text is the query; the target is the files the real fix changed that already existed at the frozen version (61 of 63 tickets scorable).
- **Baseline scores (keyword, whole files):** a changed file in the top 10 for 79% of tickets (70% without file names in the ticket, 100% with); recall@20 0.63; vague tickets weakest (hit@10 0.65); cross-repo tickets find one repo but miss the other (recall@20 0.32). Search takes about 11 ms per ticket.
- **Files:** `specbridge/code_index.py`, `specbridge/retrieval_eval.py`, `scripts/eval_retrieval.py`, `scripts/smoke_test_step4.py`, `data/retrieval/keyword.md|json`
- **Smoke test:** `scripts/smoke_test_step4.py` -> `data/smoke_test_step4.md` (now covers all of Step 4, see below).

### Step 4b - Pieces with on-screen text and screen location
- **Did:** every non-test file split into top-level pieces (3,827: components, hooks, resources, workspaces, modals, functions; tiny types merged into the next piece, long ones cut at about 1,500 tokens), each with name, kind and line range. Each piece is labelled with the English text it shows (`t('key', 'Default')` and the package's `translations/en.json`) and where its file appears in the app (widget slot, page, workspace or modal from `routes.json` and the app's `index.ts`; 605 files, 323 of them through the component that imports them). Keyword search over pieces weights the file path highest.
- **Scores:** keyword search over pieces is about equal to whole files (hit@10 0.79 both; mrr 0.50 vs 0.46). Different field weights and ways of rolling pieces up to files moved results by only 1-2 tickets (noise at 61 tickets). The pieces matter as the units the LLM reads and the embeddings cover.
- **Files:** `specbridge/code_parse.py`, `specbridge/code_index.py`, `data/retrieval/pieces.md|json`

### Step 4d - Links, combined search and agent tools
- **Did:** three kinds of links between files: relative imports (2,644); names imported from `@openmrs` packages resolved to the file in `core` that defines them (3,074); UI wiring - a slot, workspace or modal name used in one file and registered for another in `routes.json` (410, including links across repos such as the patient-chart start-visit button shown in the patient-management search banner). Combined search: keyword search over pieces, plus search by meaning when vectors exist (merged by reciprocal rank), then link-following (the top 5 files pass a share of their score to files linked by UI wiring or imports, damped for files with many links). Agent tools with JSON schemas: `search_code`, `read_file` (only files in the library), `grep`, `find_usages`.
- **Scores (combined, no embeddings):** hit@10 0.80 (0.74 without file names in the ticket), recall@10 0.58, recall@20 0.66, mrr 0.53; cross-repo recall@20 0.32 -> 0.52. Settings picked from a small grid; differences under about 0.03 are noise.
- **Files:** `specbridge/code_index.py`, `specbridge/code_tools.py`, `data/retrieval/combined.md|json`

### Step 4c - Search by meaning (built; waiting for Ollama)
- **Did:** embedder for local Ollama (`config/embedder.json`, `nomic-embed-text`, override with `EMBED_MODEL`); each piece is embedded as "repo + path, name + kind, where it appears, on-screen text, code"; vectors stored in the same SQLite file and searched exactly with `numpy` (installed in the project `.venv`). Embedding is resumable and skips pieces already done.
- **Blocked:** the Ollama install on the Linux laptop is incomplete (no `llama-server` in `/usr/local/lib/ollama`), so it cannot run any model. The user chose to reinstall it (`curl -fsSL https://ollama.com/install.sh | sh`). Then: `.venv/bin/python scripts/eval_retrieval.py --method hybrid` (embeds all pieces once, then scores) and re-run the smoke test.
- **Files:** `specbridge/embedder.py`, `config/embedder.json`, `specbridge/code_index.py`
- **Smoke test (all of Step 4):** `.venv/bin/python scripts/smoke_test_step4.py` -> 21 pass, 1 warn (combined search at 0.74 without file names, below the provisional 0.80 bar), 2 pending (live Ollama embedder; hybrid score). The 4c plumbing passes against a fake embedding server.

## Planned

### Step 5 - Live GitHub reading
Read files from GitHub at the frozen version when needed, instead of from the library. Needs a GitHub token. Compared with Step 4 in Step 10.

### Step 6 - Ticket reader
Pull requirements and acceptance criteria out of a ticket; flag vague, contradictory or unsafe tickets (hidden instructions, fake screens, secret requests). Includes the 6 adversarial tickets.

### Step 7 - Test-case writer
Write UAT test cases (steps, expected result, which code it is based on) from the ticket plus the code found in Step 4 or 5.

### Step 8 - Publish
Write the test cases as a page in Confluence space `UAT` and comment the link on the Jira ticket. Simple page or button to run it. Least-privilege bot account instead of a personal token.

### Step 9 - Golden answers and scoring
Team writes correct answers for 30-50 tickets; human rubric plus an LLM judge; set the ship gate (minimum scores to call it ready).

### Step 10 - Improve and compare
At least 3 improvement rounds, each scored on the golden set; code library against live GitHub; LLM against SLM when the SLM course needs it.

### Step 11 - Real users and course deliverables
5+ real users who are not classmates; one-page PRD; demo; 10-minute presentation.

# SpecBridge build steps

What we are building, one step at a time. After each step: report blockers, run its smoke test, and wait for "proceed" before starting the next. Keep this file updated as steps finish or the plan changes. Decisions behind the steps are in [USER_CLARIFICATIONS.md](USER_CLARIFICATIONS.md). The agent's design (Steps 6-9) is in [ARCHITECTURE.md](ARCHITECTURE.md), drawn in [architecture.drawio](architecture.drawio); the map below ties every box in the drawing to a step. What each file does is in [repo_map.md](repo_map.md): update it whenever a file is added or gains new functionality (`py -3.12 scripts/check_repo_map.py` lists files missing from it).

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
| 3 | Swappable brain: one interface for LLM and SLM | E2 | Done (SLM part waits until the SLM course needs it) |
| 4 | Code library: index the repos and search them locally (SQLite + numpy) | E4 | Done (search 0.79 vs provisional 0.80 bar on tickets without file names - see 4c) |
| 5 | Live GitHub code reading (second approach, to compare) | E4 / E5 | Moved into Step 10 (2026-10-28) |
| 6 | Ticket reader: 6a intake, 6b understand, 6c clarify (pull out requirements; flag vague or unsafe tickets) | E8-S1 | In progress - agent built node by node in `specbridge/agent/` (see "Agent nodes" below): nodes 0-11 built (START ... reviewer with its retry loop, render, save_local, publish); the whole graph has run live, including publish and a retry round |
| 7 | Agent (LangGraph): 7a skeleton + state + checkpointer, 7b code source, 7c orchestrator, 7d criterion worker, 7e e2e worker, 7f merge, 7g reviewer, 7h wire up and limits | E6, E8 | Planned |
| 8 | Output: 8a render + save_local, 8b publish to Confluence and comment on Jira, 8c command line + simple local page, 8d bot account, 8e "Run SpecBridge" button in Jira | E9, E11, E12 | In progress - 8a, 8b done (nodes 9-11); 8e built (live check from Jira pending); 8c, 8d open |
| 9 | Golden answers and scoring: rubric, LLM judge, ship gate | E10 | Planned |
| 10 | Improve over 3+ rounds; compare LLM against SLM, several workers against one, and code library against live GitHub (former Step 5) | E3, E4, E5, E10 | Planned |
| 11 | Real users (5+, not classmates), one-page PRD, demo, presentation | - | Planned |

Steps 4-11 are the current proposal and may change; each is agreed with the user before it starts.

## Architecture diagram to steps

Every box in [architecture.drawio](architecture.drawio) and the step that builds it. Build order inside Steps 6-8 follows the run order, except that Step 7a first builds the whole graph with stub nodes so every later node is added to something that already runs from START to END.

| Box in the drawing | Kind | Built in | Notes |
|---|---|---|---|
| Ticket URL (CLI or local Run page) | input | 8c | `scripts/run_ticket.py` first (7h), then the simple page |
| START, END, main graph, `SpecBridgeState` | graph | 7a | stub nodes, routers, limits as settings |
| `intake` | code | 6a | team Jira only, fetch, clean, injection flags |
| `understand` | AI | 6b | intent, criteria, screens, questions, risks, testable |
| `clarify` | code | 6c | needs-clarification result, no test cases |
| `orchestrator` | code | 7c | group (max 5), search, hand out, brief, budget split, `Send` |
| `criterion_worker` x N (subgraph) | AI agent | 7d | `receive_slice`, `agent` <-> `tools`, `write_cases`, `WorkerResult` |
| `e2e_worker` (subgraph) | AI | 7e | only when 2+ workers |
| `merge` | code + AI | 7f | combine, IDs, dedupe; AI editor |
| `reviewer` | code + AI | 7g | code checks, independent AI review, retry routing |
| `render` | code | 8a | page grouped by criterion + comment text |
| `save_local` | code | 8a | dry-run and eval mode |
| `publish` (the only writer) | code | 8b | page in `UAT`, ticket comment, never overwrite PM edits |
| Brain adapter | service | 3 (done), `chat()` added in 7d | multi-turn call for the worker's tool loop |
| Knowledge base / code source | service | 4 (done), 7b, 10 | `LibrarySource` in 7b; `GitHubSource` in Step 10 |
| Jira | service | 2 (done), 6a (read), 8b (write) | `get_issue` in 6a; comment create/update in 8b |
| Confluence | service | 8b | page find/create/update, label `awaiting-pm-review` |
| Checkpointer + run records | service | 7a | `SqliteSaver` + `data/runs/`; feeds Step 9 |
| Limits ($0.25, 2 rounds, ~12 tool calls, 20% reserve) | settings | 7a (defined), 7h (enforced) | hitting one gives status `incomplete` |

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
- **Default model:** `google/gemini-3.8-flash` through OpenRouter (switched from Claude Sonnet 5.5 on 2026-10-27).
- **Found with the live key:** Gemini 3.8 Flash "thinks" before answering, and the thinking counts against `max_tokens`. With a limit of 20 it returned an empty answer. The brain now raises a clear error in that case instead of returning empty text. Later steps must give it room (hundreds of tokens even for short answers).
- **Smoke test:** `scripts/smoke_test_step3.py` -> `data/smoke_test_step3.md` - 15 pass, 1 skipped (SLM not chosen yet). Live calls cost $0.0003 (plain) and $0.0027 (JSON; Gemini's first JSON answer was rejected and the automatic retry fixed it).

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

### Step 4c - Search by meaning (done 2026-10-27, on the Windows laptop)
- **Did:** embedder for local Ollama (`config/embedder.json`, `nomic-embed-text`, override with `EMBED_MODEL`); each piece is embedded as "repo + path, name + kind, where it appears, on-screen text, code"; vectors stored in the same SQLite file and searched exactly with `numpy` (installed in the project `.venv`). Embedding is resumable and skips pieces already done.
- **Ran on the Windows laptop** (Ollama 0.40.11 with `nomic-embed-text`; the Linux laptop's Ollama is still broken). Embedding all 3,827 pieces took 47 minutes on the processor (one time; re-runs skip done pieces). Run with `py -3.12 scripts/eval_retrieval.py --method hybrid`.
- **Scores, hybrid (keywords + meaning + links) vs combined (no meaning):**

  | Tickets | hit@10 | recall@20 | mrr |
  |---|---|---|---|
  | all (61) | 0.80 -> **0.84** | 0.66 -> **0.73** | 0.53 -> 0.54 |
  | no file names in ticket (43) | 0.74 -> **0.79** | 0.60 -> **0.70** | 0.48 -> 0.52 |
  | vague (17) | 0.59 -> **0.71** | 0.59 -> **0.73** | 0.40 -> 0.45 |
  | cross-repo (6) | 1.00 -> 1.00 | 0.52 -> 0.50 | 0.64 -> 0.81 |

  Meaning search helps most where expected: vague tickets. Tickets without file names reach 0.79, one ticket short of the provisional 0.80 bar (34 of 43; 35 needed). Search now takes about 0.5 s per ticket (was 0.03 s), still fast.
- **Fixed:** the Step 4 smoke test crashed once all pieces were embedded (it read from the database after closing it); this path had never run before.
- **Files:** `specbridge/embedder.py`, `config/embedder.json`, `specbridge/code_index.py`
- **Smoke test (all of Step 4):** `py -3.12 scripts/smoke_test_step4.py` -> `data/smoke_test_step4.md` - 23 pass, 1 warn (hybrid at 0.79 without file names, just below the provisional 0.80 bar), 0 pending.

### Agent nodes (from 2026-11-06)
Steps 6-8 are built **node by node in the order of [architecture.drawio](architecture.drawio)**: START (0), intake (1), understand (2), clarify (3), orchestrator (4), criterion_worker (5), e2e_worker (6), merge (7), reviewer (8), render (9), save_local (10), publish (11). For each node the user approves a spec (behaviour, edge cases, tests) before code is written; the graph grows by one node each time. Code in `specbridge/agent/`, prompts in `prompts/`, tests in `tests/agent/` (pytest). Packages pinned in `requirements.txt`.

#### Node 0 - START (done 2026-11-07)
- **Did:** `scripts/run_ticket.py <ticket URL or key> [--mode dry-run|eval] [--run-id ID --resume] [--no-preflight]` -> `run_ticket()` in `specbridge/agent/graph.py`. Checks the request (reference not empty, at most 2,000 characters; mode `dry-run` or `eval`, `live` refused until publish exists; safe run id); loads and checks `config/agent.json` (defaults if missing); brain check (`preflight.py`: key set; OpenRouter accepts it, its spending limit is not used up, the model is offered; low account credit only a warning because BYOK calls still work; no question sent to the model); creates the run; runs START -> intake (placeholder) -> END with a SQLite checkpointer in `data/runs/checkpoints.sqlite`; writes `data/runs/<ticket>/<run_id>.json` however the run ends (complete, paused, error, interrupted). Paused, crashed and Ctrl-C runs resume with `--resume --run-id`. `data/runs/` is git-ignored.
- **Files:** `specbridge/agent/graph.py`, `state.py`, `limits.py`, `preflight.py`, `run_record.py`, `nodes/intake.py` (placeholder), `config/agent.json`, `scripts/run_ticket.py`, `tests/agent/conftest.py`, `tests/agent/test_start.py`
- **Tests:** `.venv/bin/python -m pytest tests/agent/test_start.py` -> 61 pass (including the live brain check and a live command-line run).

#### Node 1 - intake (done 2026-11-07)
- **Did:** `specbridge/agent/nodes/intake.py` replaces the placeholder; the graph is START -> intake -> END. Reads the reference (ticket URL, board link with `selectedIssue=`, or the key, any case); refuses anything that is not https on exactly `ATLASSIAN_SITE` (other hosts, look-alikes, `user@host`, IPs, other ports) or not project `SPEC`, before any network call; fetches summary, type, status, labels and description read-only (one retry on 429/5xx/network; 404, 401/403 and others give clear messages; the token never appears). `specbridge/ticket_text.py` turns the rich text into plain text that keeps headings, numbered / bulleted / nested lists, code blocks, quotes and tables; drops images, shows @mentions as "(someone)" and links as their text only. Secrets (passwords, API keys, tokens, JWTs, private keys) become `<redacted-secret>` in the title, text and labels before anything is stored; lines aimed at the AI are flagged `possible-injection` and kept. Other flags: `empty-description`, `truncated` (over 20,000 characters), `attachments-dropped`, `mentions-files`. Any status is accepted. Output: `state["ticket"] = {key, url, type, status, title, text, labels, flags}`; the command line prints it. A failure ends the run with status `error`; network failures can be resumed.
- **Also:** the Jira client moved from `scripts/atlassian.py` to `specbridge/atlassian.py` (new `get_issue`, `JiraError` with the HTTP status); `import_tickets.py`, `import_adversarial.py` and `smoke_test_step2.py` import it from there. The Step 2 smoke test's folder-size check now counts only files git would track (it had started counting the git-ignored `.venv`).
- **Checked on all 69 real tickets:** every one fetches and cleans; only SPEC-65 has secrets redacted (both planted secrets gone, "password field" text untouched) and only SPEC-66 is flagged for instructions to the AI; 18 tickets name code files; text is 153-5,537 characters.
- **Files:** `specbridge/agent/nodes/intake.py`, `specbridge/ticket_text.py`, `specbridge/atlassian.py`, `scripts/run_ticket.py`, `tests/agent/test_intake.py`, `tests/agent/conftest.py` (fake Jira), `tests/agent/fixtures/jira/` (8 saved real tickets)
- **Tests:** `.venv/bin/python -m pytest tests/agent` -> 183 pass (4 live: all 69 tickets, fixtures still match Jira, the live brain check and a live command-line run).

#### Node 2 - understand (built 2026-11-09; full sweep pending)
- **Did:** `specbridge/agent/nodes/understand.py` with `prompts/understand.md` (`understand-v1`); the graph is START -> intake -> understand -> END. One `ask_json` call (Gemini 3.8 Flash, fixed schema, 4,000 tokens for thinking) with the cleaned ticket inside a `<ticket>` data block, intake's flags and a short description of OpenMRS and its five apps. The answer gives intent, criteria (`stated` with an exact quote, or `inferred`; `ok` / `conflicting` / `unclear`), screens (`changed` / `used`), roles, questions, risks and `domain_fit` (fits / doubtful / unrelated). Code then checks it: a stated criterion whose quote is not in the ticket becomes inferred; ids are renumbered AC1..; intake's flags always become risks (`secret-in-ticket`, `injection-attempt`, `partial-ticket`); conflicting criteria add `contradictory`; more than 15 criteria add `too-broad`; every screen is looked up in the code library (`CodeIndex.find_screen`: unknown only if one of its words appears nowhere in the code); `doubtful` / `unrelated` add `off-domain` and a question. Testable is decided by rules: not testable if backend-only, unrelated to the product, the screen to change is not in the code, or no usable criterion is left; text asking the AI to skip test cases cannot make a ticket untestable. The answer is redacted once more. Spending goes into `state.spent`; model, prompt version, tokens, cost and time into `understanding.meta`. An AI failure (busy, invalid JSON twice, out of tokens, out of credit) ends the run with status `error` and can be resumed.
- **Also:** `ticket_text.py` (rewritten by the team) got the two lost AI-instruction patterns back in a narrow form ("QA sign-off: complete", "include the admin password"); 3 intake tests were updated to its new formatting. Offline tests now block the network (a test that reaches it fails), and `start()` in the tests uses a fake AI.
- **Checked live:** SPEC-66 is testable with `injection-attempt` (the ticket's "do not write test cases" ignored); all 6 trick tickets (SPEC-64..69) and the 4 hand-written off-domain tickets (`data/golden/off_domain_v0.json`: flight booking and a Bitcoin wallet -> unrelated, not testable; a quote of the day -> testable; blood group in the banner -> fits) give the expected result. About 10-25 s and $0.005 per ticket (some calls $0 through the team's own Gemini key).
- **Brain switched (2026-11-09):** OpenRouter dropped; Gemini is called directly at Google (`config/brains.json`, `GEMINI_API_KEY`). `brain.py` now estimates cost from list prices when the provider reports none and counts hidden thinking tokens; `preflight.py` checks the key by listing Google's models; `tests/test_brain.py` added; the Step 3 smoke test follows.
- **Screens grounded in the code (2026-11-09, ADR D20, `understand-v2`):** the first 43 real tickets ran on v1 (38 testable; 5 not: SPEC-3 backend-only, SPEC-35 nothing checkable, and SPEC-14 / 32 / 39 wrongly blocked because they build new screens or named a technology). Now understand is shown the ~25 registered screens most related to the ticket (`CodeIndex.screens_for`), labels each screen existing / new, and only an existing screen missing from the code blocks the ticket.
- **Test scope (2026-11-09, ADR D21, `understand-v3`):** each ticket gets `test_scope` = full / regression / none. A backend-only change to the code of an existing screen found in the code (SPEC-3) is testable with a regression check of `regression_screens`; other backend-only tickets (SPEC-68) go to clarify. Re-running from understand when the PM answers in Jira is planned in the ADR, not built.
- **Pending:** the sweep over all 69 tickets (`scripts/eval_understand.py`) stopped after 8 tickets because the OpenRouter key ran out of credit (HTTP 402). Of the 8, only SPEC-3 was not as expected: judged backend-only, and its text does say it "does not technically cause any user-facing issues" - to be decided whether such real tickets should count as testable.
- **Files:** `specbridge/agent/nodes/understand.py`, `prompts/understand.md`, `specbridge/code_index.py` (`find_screen`), `specbridge/ticket_text.py`, `scripts/eval_understand.py`, `scripts/run_ticket.py`, `data/golden/off_domain_v0.json`, `tests/agent/test_understand.py`, `tests/agent/conftest.py`
- **Tests:** `.venv/bin/python -m pytest tests/agent -m "not live"` -> 215 pass; `-m live` -> the 10 understand live tests passed (run before credit ran out).

#### Node 3 - clarify (done 2026-11-09)
- **Did:** `specbridge/agent/nodes/clarify.py` (code only). The graph now branches: START -> intake -> understand -> clarify -> END when the test scope is `none`; for `full` / `regression` it ends after understand (status `complete`, note "the orchestrator (node 4) is not built yet") until node 4 exists. clarify picks the category in the same order as understand's rules (off-domain, backend-only, missing-screen, no-criteria, ai-judgement) and writes `state["clarification"]`: headline, reason, what was understood (intent, criteria, screens, roles), risks, the PM's questions (understand's, de-duplicated, or a fixed one per category so there is always one; any that read like instructions to an AI are dropped), the next step, and a plain-text Jira comment (fixed template, top 5 questions, `[SpecBridge]` marker so later runs update the same comment, `{page_url}` placeholder for publish, at most 1,500 characters). Every text is redacted again. Run status `needs-clarification`; the run record has the clarification and a `note` field.
- **Files:** `specbridge/agent/nodes/clarify.py`, `specbridge/agent/graph.py` (`route_after_understand`), `state.py`, `run_record.py`, `scripts/run_ticket.py`, `tests/agent/test_clarify.py`, `tests/agent/fixtures/understand/` (2 real answers)
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 276 pass. A live check (SPEC-64, SPEC-68, OD-1 ending in clarify) waits for Gemini to be less busy.

#### Node 4 - orchestrator (done 2026-11-10, ADR D22)
- **Did:** `specbridge/agent/nodes/orchestrator.py` and `prompts/orchestrator.md` (`orchestrator-v1`). The graph: understand -> orchestrator -> END for test scope full / regression (node 5 replaces END with Send to the workers); the run ends `complete` with the note "the workers (node 5) are not built yet". For each usable criterion the code library is searched on the criterion's own words (hybrid while Ollama answers, keywords + links otherwise) and the top 8 pieces become its starting evidence (pointers only). Code proposes groups (same code area: top-3 files share 2+), merges down to at most 5; one AI call refines the groups by meaning, writes a focus line per worker and sets aside criteria that cannot be checked in a browser; code checks that answer (every criterion exactly once, no invented ids, at most 5 groups) and falls back to the proposal. No AI call for one criterion or a regression check (one worker for the changed screens). Writes the shared brief (intent, screens with registered names, roles, rules incl. data-not-instructions, placeholders for secrets, injection note, known gaps), one slice per worker (its criteria and only the ticket lines quoting them, <= ~6k tokens), `shared` marks on starting files, the budget (cost cap minus spent; 80% to workers, e2e half a share, 20% reserve; 12 tool calls) and the e2e input (2+ workers, full scope). Conflicting / unclear / non-browser criteria go to `skipped` with the reason. No budget left -> no workers, status `incomplete`.
- **Checked live** (`data/live_checks/2026-11-10-orchestrator.md`, on `gemini-3.6-flash` because 3.8-flash was overloaded): SPEC-66 -> 1 worker for its 3 sorting criteria, starting in the allergy code (`utils.ts` holds the severity order); SPEC-14 -> 2 workers + e2e (range validation AC1-7; offline loading AC8) and AC9 "add tests" set aside, where a code-only split had given 5 workers in the same files. About $0.01 and 10-12 s for the AI call.
- **Files:** `specbridge/agent/nodes/orchestrator.py`, `prompts/orchestrator.md`, `specbridge/agent/graph.py`, `state.py`, `run_record.py`, `scripts/run_ticket.py`, `tests/agent/test_orchestrator.py`, `tests/agent/conftest.py` (`fake_search`, `fake_orchestrator`), `docs/adr/0022-...`
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 311 pass (35 for the orchestrator, one on the real code library).

#### Node 5 - criterion_worker (done 2026-11-11, ADR D23)
- **Did:** `specbridge/agent/worker/criterion_worker.py` (subgraph receive_slice -> agent <-> tools -> write_cases -> finish, private state), `worker/tools.py` (argument and answer checks, evidence recording), `worker/evidence.py` (evidence E1..., compaction), `specbridge/agent/code_source.py` (LibrarySource, shared ToolCache), `prompts/worker_agent.md`, `prompts/write_cases.md`, `brain.chat()` (multi-turn) and `load_brain(role=...)`. The orchestrator now `Send`s one worker per work item, in parallel; results are appended to `state.results`; a crashed worker becomes status `error` and the others carry on; the run ends `complete` or `incomplete` (any worker not complete) with the note "merge (node 7) is not built yet". Search turns use `gemini-3.5-flash-lite`, `write_cases` the main model; 8 tool calls per worker.
- **Checked live** (`data/live_checks/2026-11-11-criterion-worker.md`): SPEC-66 -> 1 worker, 7 tool calls, 6 cases covering AC1-AC3, each citing code it read (`severityOrder` in `utils.ts`, the allergies list extension); $0.057 for the whole ticket, 119 s. SPEC-14 -> 3 parallel workers; its code (the Angular form engine) is not in the frozen repos, so the workers marked 8 criteria untestable with reasons and wrote 2 cases for the offline fallback; $0.10, 132 s.
- **Open points for later nodes:** a worker with all criteria untestable is `complete` with 0 cases (merge / reviewer / page must show it); the orchestrator's AI split varies by model (SPEC-14: 2 workers on 3.6-flash, 3 on 3.8-flash).
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 348 pass (37 for the worker).

#### Node 6 - e2e_worker (done 2026-11-11)
- **Did:** `specbridge/agent/worker/e2e_worker.py` and `prompts/e2e.md` (`e2e-v1`). The orchestrator's `Send`s now include one e2e worker when it planned 2+ criterion workers in full scope; it runs in parallel with them and independent of them (D17). It is the criterion worker's subgraph in "e2e" mode: a one-line summary of every criterion, no starting files, 4 tool calls to confirm screens and navigation, then 1-3 flows each through 2+ criteria and citing code it read (single-criterion, uncited, invented-id, incomplete or injected flows are dropped). No flow is a valid answer (status `complete`, with the reason); stopped by a limit before finding code -> `budget_hit`; a crash -> `error`, the other workers carry on.
- **Choices** (not answered explicitly, so the recommended ones): parallel and independent; strict citations; 4 tool calls; at most 3 flows; reuse of the criterion worker's subgraph.
- **Checked live** (`data/live_checks/2026-11-11-e2e-worker.md`): SPEC-12 -> 3 criterion workers + e2e, 13 cases + 2 flows, all citing `conditions-form.workspace.tsx` (the file the real fix changed); $0.129, 297 s. Research was thin (three workers read one file in 2 tool calls; one cited a test file) - for the reviewer and Step 10.
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 367 pass (19 for the e2e worker).

#### Node 7 - merge (done 2026-11-11, ADR D24)
- **Did:** `specbridge/agent/nodes/merge.py` and `prompts/merge_editor.md` (`merge_editor-v1`). The graph: criterion workers + e2e worker -> merge (runs once, after all of them) -> END; the run ends with the note "the reviewer (node 8) is not built yet". Code builds `state["plan"]`: newest result per worker, one evidence list EV-01.. (exact and contained ranges merged, citations rewritten), cases TC-01.. ordered by criterion and type (flows last) with their source, a coverage status per criterion (covered / untestable / uncovered / skipped / failed / regression), common preconditions (in at least half of the cases), de-duplicated questions and notes. With 2+ workers or more than 8 cases one AI call may suggest only `remove` (duplicate) and `rename`; code accepts a removal only with the same criteria, the same type and 60%+ the same steps, never a criterion's last case, and a rename only to a real name; then whole-plan checks, all or nothing; every suggestion is listed in `plan["changes"]`.
- **Choices:** the recommended ones (AI pass with strict operations, notes stay notes, AI pass only for 2+ workers or > 8 cases, common preconditions by code, exact and contained evidence merged), plus the user's: no `rewrite` operation, and the two extra checks on removals and renames.
- **Checked live** (`data/live_checks/2026-11-11-merge.md`): SPEC-12's 15 cases -> TC-01..15, 8 citations -> 4 evidence entries, 2 common preconditions, AC1-AC6 covered; the AI suggested no change; $0.008.
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 396 pass (29 for merge).

#### Node 8 - reviewer (done 2026-11-11, ADR D25)
- **Did:** `specbridge/agent/nodes/reviewer.py` and `prompts/reviewer.md` (`reviewer-v1`, now `reviewer-v3`: one call per criterion, and the old behaviour in the code is expected for a requested change). The graph: merge -> reviewer -> (weak criteria, round 1, budget and time left: orchestrator again | END); render (node 9) replaces END. Code checks flag cases and never drop them (evidence not in the plan, file / lines not at the frozen version, unknown quoted labels, test-file-only citations, AI-directed text; secrets redacted). Independent AI review, one call per criterion in parallel (plan B; role `reviewer`, `gemini-3.6-flash` for now, prompt `reviewer-v3`): each call sees one criterion, its cases, flags and only the code they cite, re-read from the library, never the workers' reasoning; a reply without its own verdict is asked once more, then counted as failed. A criterion is weak if it has no case and no reason, or the AI says so; untestable and skipped criteria pass through. One retry round: `orchestrator.retry_plan` (weak criteria only, the reviewer's problems and hint in the slice, round-1 code as starting pointers, 90% of the remaining budget, no e2e); `merge.combine_rounds` (round-2 cases replace a criterion's only if there are any); the second review re-judges only the retried criteria. Final status `complete` / `incomplete` with the reason; a failed AI review is stated in the reason.
- **Choices:** the user's: `gemini-3.6-flash` for the reviewer (3.8-flash was overloaded), one AI call per criterion in parallel (plan B, chosen after plan A was built; about 2.5x the cost, stricter), one retry, a retry never makes a criterion worse, flag instead of drop.
- **Checked live** (`data/live_checks/2026-11-11-reviewer.md`): SPEC-12's real plan -> all 6 criteria ok ($0.020); with a planted ungrounded case -> that criterion weak with a precise grounding problem and hint, plus a code flag for the invented label ($0.016). Fixed on the way: `translations/en.json` was wrongly flagged as missing (now read from the frozen checkout).
- **Run live since:** a full ticket through the retry loop (SPEC-66, 2026-11-11, `data/live_checks/2026-11-11-publish.md`).
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 419 pass (24 for the reviewer and the retry loop); 425 after plan B and `reviewer-v3`.

#### Node 9 - render (done 2026-11-11, ADR D26)
- **Did:** `specbridge/agent/nodes/render.py` (code only, `render-v1`). The graph: reviewer (final) -> render, clarify -> render, orchestrator (nothing to send or incomplete) -> render; render -> END until save_local exists. One document is written as Confluence storage format, a standalone HTML page and a Markdown copy, plus the Jira comment (`[SpecBridge]` marker, `{page_url}`, at most 1,500 characters) - `state["page"]` = title, labels, storage, html, markdown, comment, summary. Three kinds of page: test plan (summary and screens, common preconditions, cases by criterion with status tags and the reviewer's problems, flows, open questions, notes, review report, evidence links at the frozen commit, run details), clarification (questions only), and stopped early (the reason). All text redacted again and escaped; AI-directed questions and notes left out; same state and clock -> same output. The run record keeps the page without the HTML and Markdown copies.
- **Choices:** the user's: a Markdown copy as well, 6 columns; the recommended ones: flags in a row under their case, flows in their own section, GitHub links without code, weak criteria shown with their cases, notes collapsed, file copies not in the run record.
- **Checked live** (`data/live_checks/2026-11-11-render.md`): SPEC-12's real plan with a live review ($0.052 for the review, $0 for render, 22 ms, 30 KB) and SPEC-64's saved clarification record ($0). Fixed on the way: bold labels in Markdown, double step numbers, stop codes in words, the clarification page's wording.
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 449 pass (24 for render).

#### Node 10 - save_local (done 2026-11-11)
- **Did:** `specbridge/agent/nodes/save_local.py` (code only). The graph: render -> (dry-run / eval: save_local | live: publish, not built yet) -> END. Writes `data/runs/<ticket>/<run_id>/page.html`, `page.md`, `page.storage.xml` and `comment.txt` (with `{page_url}`) next to the run record, which `run_ticket` still writes at the end. Folder from the checked key and run id only, never outside `data/runs/`; each file written to a temporary name and renamed, with normal permissions; a last secret scan and XML check give warnings; a write error is reported in `state["saved"]` and the run note, the command exits with 1, and the run is kept. `run_ticket.py` prints where the page was saved. The run record keeps `saved`.
- **Choices:** the recommended ones (the user: "yes"): a folder per run next to the record, `{page_url}` kept, no "latest" copy, the same files in eval mode, write errors reported (exit 1), one full live run.
- **Checked live** (`data/live_checks/2026-11-11-save-local.md`): the first full run through every node - SPEC-66 in dry-run, `complete`, 6 cases, 3/3 criteria ok, $0.073, 97 s in the nodes. `gemini-3.8-flash` was hanging at Google, so the run was resumed from its checkpoint with the main model on `gemini-3.6-flash`. Fixed after the run: private file permissions, "1 open questions". Found for node 5: a case type `empty-state` outside happy / negative / edge, which made the reviewer flag a missing edge case.
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 470 pass (20 for save_local).

#### Node 11 - publish (done 2026-11-11, ADR D27)
- **Did:** `specbridge/agent/nodes/publish.py` (code only) and the write calls in `specbridge/atlassian.py`. The graph: render -> (dry-run / eval: save_local | live: publish) -> END; live mode is now allowed, and START checks the Atlassian settings and the Confluence space before any AI call (`preflight.check_atlassian`). Checks before any write (project, site, page, XML, size, no secrets); the page found by labels (ticket key + `specbridge`) or title; created with labels and a `specbridge` property, updated only if SpecBridge wrote its current version, otherwise the draft goes in as a page comment (D10); one `[SpecBridge]` Jira comment per ticket with the page link; failures reported (note, exit 1) and the page saved locally. `run_ticket.py --mode live` prints the page address.
- **Choices:** the recommended ones ("complete next node").
- **Checked against the real site (read-only):** the space, the label search, the account and the comments on SPEC-66. Found: the space's real key is `SU` (`UAT` is an old alias), so publish uses the key Confluence reports; the token in `.env` belongs to Hussain Lohawala, so writes appear under that name until the bot account (8d) exists.
- **Checked live** (`data/live_checks/2026-11-11-publish.md`, after the user's go-ahead): SPEC-66 run 1 created the page (<https://rooks101.atlassian.net/wiki/spaces/SU/pages/5111809>) with its labels and property, and one Jira comment ($0.065); run 2 updated the same page to version 2 and the same comment ($0.095). Run 2 was also the first live retry round: a Google 503 cut the worker's search short, the reviewer sent AC2 and AC3 back, and the retry worker's cases passed the second review. Not run live: a person's edit between runs (covered offline).
- **Also on 2026-11-11:** the main model is `gemini-3.6-flash` for now (3.8-flash kept hanging), and the reviewer's "no negative or edge case" check now counts every non-happy case type (`permission`, `empty-state` too).
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 500 pass (27 for publish).

## Planned

### Step 5 - Live GitHub reading (moved into Step 10)
Moved on 2026-10-28: the agent works on the code library alone, and the comparison is only meaningful once the agent exists. Findings so far, for when it is built: GitHub's code search covers only the latest code (which already contains the fixes), so at the frozen version the live approach can only list folders, read files and search inside files already read; it needs a GitHub token (60 calls/hour without one); and on this Windows laptop one of GitHub's four addresses (185.199.109.133) does not answer, so Python waits 21 s per connection unless the client skips it.

### Step 6 - Ticket reader (`intake`, `understand`, `clarify`)
Pull requirements and acceptance criteria out of a ticket; flag vague, contradictory or unsafe tickets (hidden instructions, fake screens, secret requests). Includes the 6 adversarial tickets (hand-written, in Jira as SPEC-64 to SPEC-69, see [repo_map.md](repo_map.md)). Gemini 3.8 Flash thinks before answering and the thinking counts against `max_tokens` (Step 3), so every AI call here needs room: hundreds of tokens even for short answers. Smoke test for the whole step: `scripts/smoke_test_step6.py` -> `data/smoke_test_step6.md`.

#### 6a - `intake` (code, no AI)
- **Build:** `specbridge/tickets.py`. Accept a full ticket URL, a board link with `selectedIssue=`, or just `SPEC-12`. Check the site and project are the team's (`ATLASSIAN_SITE`, `JIRA_PROJECT_KEY`); fetch summary, type, description, labels and acceptance-criteria fields; turn Jira rich text into plain text (reuse the cleaner in `scripts/import_tickets.py`); drop images; keep link text, not link targets; flag text that looks like instructions to an AI or asks for secrets. Add `get_issue` to `scripts/atlassian.py`.
- **Output:** `Ticket {key, url, type, title, text, labels, flags[]}`.
- **Smoke test:** all 69 tickets (SPEC-1..69) fetch and clean; a URL for another site or project is refused; the hidden-instruction and secret-request adversarial tickets are flagged; no token appears in any output.

#### 6b - `understand` (one structured AI answer)
- **Build:** `specbridge/understand.py` and `prompts/understand.md`. One `ask_json` call with a schema: `intent`, `criteria[] {id, text, source: stated | inferred}`, `screens_mentioned[]`, `user_roles[]`, `questions[]`, `risks[]`, `testable` (yes/no with a reason). Ticket text goes into the prompt inside a marked data block with a standing rule to ignore instructions found there.
- **Smoke test:** on the 10 golden examples in [golden_set_eval_rubric_v0.md](golden_set_eval_rubric_v0.md) and the 6 adversarial tickets: criteria are extracted, a ticket without criteria gets some marked `inferred`, fake-screen / backend-only / contradictory / secret / injection tickets come out `testable = no` or carry the right risk. Live cost recorded.

#### 6c - `clarify` (code)
- **Build:** the "needs clarification" result: the questions and risks, and no test cases. The main graph routes here when `testable = no` or the ticket is unsafe (wired in 7a).
- **Smoke test:** every ticket judged not testable produces questions and zero cases; the result can be rendered later by `render` (8a).

### Step 7 - Agent: orchestrator and subagents (LangGraph)
The graph in [ARCHITECTURE.md](ARCHITECTURE.md): an orchestrator splits the ticket by acceptance criterion; independent criterion workers (subgraphs) search the code with read-only tools and write cases citing evidence; merge combines; an independent reviewer checks coverage and grounding and sends weak criteria back (max 2 rounds). New packages: `langgraph` 1.2.x and `langgraph-checkpoint-sqlite` 3.1.x, pinned to exact versions at install time (check they support Python 3.12). Nodes are plain functions that call our own brain adapter; no LangChain model wrappers, no prebuilt `ToolNode` / `create_react_agent` (D1, D6). Smoke test for the whole step: `scripts/smoke_test_step7.py` -> `data/smoke_test_step7.md`.

#### 7a - Skeleton: state, graph, checkpointer
- **Build:** `specbridge/graph.py`. `SpecBridgeState` and `WorkerState` as in ARCHITECTURE.md section 5, with a list reducer for `results[]`. Every node (`intake` to `save_local`) exists as a stub that returns canned data; the real conditional edges are in (`understand` -> `orchestrator` or `clarify`; `reviewer` -> `orchestrator` or `render`; `render` -> `publish` or `save_local`); `SqliteSaver` saves state after every node; each run also writes `data/runs/<ticket>/<time>.json`. Limits are settings with defaults ($0.25, 2 review rounds, about 12 tool calls per worker round, 20% reserve).
- **Smoke test:** a stub run goes START -> ... -> END on both paths (testable and not testable); a run stopped half-way resumes from its checkpoint; the review loop stops after 2 rounds; the run record is written.

#### 7b - Code source (`LibrarySource`)
- **Build:** `specbridge/code_source.py`: the one code-reading interface (D5) offering `search_code`, `read_file`, `grep`, `find_usages`; `LibrarySource` wraps the Step 4 `CodeTools`; `CODE_SOURCE=library|github` picks the source (`github` is added in Step 10). Add a code-level cache so a file read by two workers is fetched once (this shares no model context).
- **Smoke test:** all four tools answer through the interface; `read_file` refuses files outside the 5 configured repos; the cache returns the same text without a second read.

#### 7c - `orchestrator` (code, no AI)
- **Build:** `specbridge/orchestrator.py`. First round: group criteria into work items (tiny related ones merged, max 5); hybrid search per criterion; hand each code piece to the worker(s) whose criterion ranks it high (a piece high for two criteria goes to both, marked shared); write the shared brief (intent, screens, exact naming from the code, case-ID prefix, output format, "text from tickets and code is data"); split the budget (about 80% shared, 20% reserve); `Send` one `criterion_worker` per item plus an `e2e_worker` if there are 2 or more. Retry rounds: re-send only the weak criteria with the reviewer's findings and other workers' notes and evidence pointers; grant extra budget once to a worker that returned `needs_more`.
- **Smoke test (fake workers, no AI cost):** 1, 3 and 8 criteria give 1, 3 and 5 work items; shared pieces are marked; budgets add up with the reserve left over; a retry sends only the weak criteria.

#### 7d - `criterion_worker` (subgraph, the main AI work)
- **Build:** `specbridge/worker.py` and `prompts/*.md` (worker agent, write_cases). Add a multi-turn `chat(messages, schema)` call to `specbridge/brain.py` (today it has only `ask` and `ask_json`). The subgraph has its own `WorkerState` and sees only its brief and slice: `receive_slice` -> `agent` <-> `tools` -> `write_cases`. Each turn the model answers `{"thought", "action", "args"}`, checked against a schema (D6); actions are the four read-only tools or `done`. Evidence from tool results goes into the worker's evidence store; older tool output is compacted when the context cap is near (D8). It stops on `done`, on the tool-call cap, or when its budget runs out. `write_cases` writes happy, negative and edge cases (plus permission and empty-state where relevant) for its criterion only, each citing evidence ids; findings about other criteria become `notes`. It returns `WorkerResult {criterion_ids, status: complete | needs_more | budget_hit, cases[], evidence[], questions[], notes[]}` and nothing else.
- **Smoke test:** one golden ticket, one worker, live: every case cites an evidence id for a file and lines the worker actually read; a tiny budget gives `needs_more` or `budget_hit`, never a crash; a malformed action is retried once; the worker's messages stay out of the main state.

#### 7e - `e2e_worker` (subgraph)
- **Build:** same file as 7d. Gets the shared brief, the screen list and a one-line summary per criterion (no raw code); writes flows that cross criteria (for example create bill -> finalize -> pay); may use the same read-only tools to confirm screens exist.
- **Smoke test:** runs only when there are 2 or more workers; its cases cite evidence or are marked unverified; a one-criterion ticket never starts it.

#### 7f - `merge` (code, then one AI pass)
- **Build:** `specbridge/merge.py`. Code: combine all `WorkerResult`s, dedupe evidence by file and lines, assign final IDs (TC-01, TC-02, ...), group by criterion. AI editor: remove duplicate cases, make screen and button names consistent, move shared setup into common preconditions, turn notes into preconditions or end-to-end cases. It may not add claims or evidence; code re-checks that every evidence id still exists afterwards.
- **Smoke test:** two workers that cite the same file give one evidence entry; a planted duplicate case is removed; an editor answer that invents an evidence id is rejected.

#### 7g - `reviewer` (code checks, then independent AI review)
- **Build:** `specbridge/review.py` and `prompts/reviewer.md`. Code checks: every criterion has a case; every case cites an existing evidence id; cited files and lines exist at the frozen version; named screens and labels appear in the code's on-screen text or `routes.json`; each criterion has a negative or edge case where it makes sense; no secrets or injected instructions in the output. AI review in a fresh context (ticket, merged cases and cited code only; ideally a different model family from the writers) gives `ok` or gaps per criterion. Route: gaps and fewer than 2 rounds -> `orchestrator` (weak criteria only); otherwise -> `render`.
- **Smoke test:** planted bad cases (a screen that does not exist, a case with no citation, a secret-like string) are each caught by the code checks; a retry re-runs only the weak criterion; the second round ends the loop.

#### 7h - Wire up, limits and a first dry run
- **Build:** replace the stubs in `graph.py` with the real nodes; enforce the limits (cost cap, 2 rounds, tool-call cap), with a hit giving status `incomplete` and never a silent failure; `max_concurrency` setting (parallel on the cloud LLM, 1 at a time on a local SLM); `scripts/run_ticket.py <ticket URL> --dry-run [--brain llm|slm] [--source library] [--max-workers 5]`; prompt versions saved in the run record (D12). `render` and `save_local` are still stubs that write the merged plan to the run record.
- **Smoke test:** the first 10 golden tickets run end to end in dry-run; one `understand`-unsafe ticket ends at `clarify` with no cases; cost, time, tokens, workers and rounds are in each run record; a run forced over the cost cap ends `incomplete`.

### Step 8 - Output: page, publish, trigger
The last part of the graph: turn the plan into a Confluence page, publish it, and give people a way to start a run. Smoke test for the whole step: `scripts/smoke_test_step8.py` -> `data/smoke_test_step8.md`.

#### 8a - `render` and `save_local` (code, no AI)
- **Build:** `specbridge/render.py`. Page: summary and intent; affected screens; test cases grouped by criterion (ID, Preconditions, Action, Expected result, Actual result left blank, Pass/Fail left blank); open questions; the review report, with any incomplete criterion marked; evidence list (file and lines); run details (model, workers, cost, time, version). Output in Confluence format and as local HTML, plus the Jira comment text. `save_local` writes the page and run record to files (dry-run and eval mode). A `clarify` result renders as a questions-only page.
- **Smoke test:** a saved run record renders with no network; the blank columns are blank; a needs-clarification record renders without cases; every evidence entry shows file and lines.

#### 8b - `publish` (the only node that writes)
- **Build:** `specbridge/publish.py`; extend `specbridge/atlassian.py` with page find/create/update and comment create/update. Create or update the page in space `UAT`, found by ticket key, labelled with the key and `awaiting-pm-review`; add or update one comment on the ticket linking to it. If someone other than SpecBridge edited the page since the last run, the new draft goes in as a comment on the page instead (D10). Scan the output for secret-like text before publishing.
- **Smoke test:** run the same ticket twice -> one page, one comment; edit the page by hand, run again -> the edit survives and the new draft appears as a comment; a write outside `UAT` or to another ticket is refused; a planted secret blocks publishing.

#### 8c - Command line and simple local page
- **Build:** finish `scripts/run_ticket.py` (live mode; `--dry-run` already exists from 7h) and `app/`: a local page where you paste a ticket URL, press Run, see progress per node and worker, and see the result (D14). A Jira webhook comes later and is not part of this step.
- **Smoke test:** a URL pasted in the page runs the graph and shows the same output as the command line; the page refuses a URL from another site.

#### 8d - Least-privilege bot account
- **Build:** replace the personal Atlassian token with a bot account that can read the `SPEC` project and write only to space `UAT` and ticket comments (open since Step 2). Update `.env.example` and README.
- **Smoke test:** the bot can publish a page and a comment; the same token cannot edit a ticket or write to another space.

#### 8e - "Run SpecBridge" button in Jira (built 2026-11-12, ADR D28)
- **Did:** `specbridge/service.py` and `scripts/serve.py` (standard library only), the guide `docs/DEPLOY_JIRA.md`, `SPECBRIDGE_WEBHOOK_SECRET` in `.env.example`, and `daily_budget_usd` / `queue_max` / `ticket_cooldown_seconds` in `config/agent.json`. A Jira Automation rule (manual trigger) sends `POST /run {"key": "{{issue.key}}"}` with a secret header through a Cloudflare quick tunnel to the service on `127.0.0.1:8765`. The service checks the request (secret in constant time, project key, body size and type), refuses double clicks, a 10-minute repeat, a full queue and the daily limit, answers 202 at once, and runs the tickets one at a time in live mode. The ticket's one `[SpecBridge]` comment says "Generating UAT test cases for PM and engineering review" at once, publish replaces it with the result, and it says so if the run fails or the limit is reached. The queue and the day's spending survive a restart (`data/service/`, git-ignored). `--dry-run` writes nothing to Jira.
- **Choices:** the user's: option B (button + webhook), the recommended settings, and better wording for the "working on it" comment.
- **Checked live on this machine** (`data/live_checks/2026-11-12-jira-button.md`): a wrong secret -> 401; the request -> 202 in 2.2 s and the "Generating..." comment on SPEC-66; a double click -> one run; the run -> page version 3 and the same comment with the result ($0.072); a repeat -> 429 for 10 minutes. **Still to do with the user:** the secret in `.env`, `cloudflared`, the Jira rule, and pressing the button in Jira.
- **Tests:** `.venv/bin/python -m pytest tests -m "not live"` -> 537 pass (37 for the service: every refusal, double click, cooldown, queue, daily limit and next day, failures and their comments, redaction, dry-run, restart, startup refusals, no secret in the log).

### Step 9 - Golden answers and scoring
Started early as course activity 3: [golden_set_eval_rubric_v0.md](golden_set_eval_rubric_v0.md) has the first 10 labelled examples, rubric v0 and the scoring split. Step 9 extends it to the full 30-50 and automates the scoring.

Team writes correct answers for 30-50 tickets; human rubric plus an LLM judge; set the ship gate (minimum scores to call it ready). `scripts/eval_agent.py` runs the exact same graph in eval mode (no publishing, output kept by `save_local`) and scores each run record: retrieval, coverage, grounding (from the reviewer's code checks), rubric and judge quality, safety on the adversarial tickets, and tokens, cost and time per node and per worker (ARCHITECTURE.md section 7). The judge should be a different model family from the writers.

### Step 10 - Improve and compare
At least 3 improvement rounds, each scored on the golden set. Comparisons on the same golden tickets: several workers against one; LLM against SLM when the SLM course needs it; code library against live GitHub. Live GitHub (former Step 5) is built here as `specbridge/code_source.py` `GitHubSource`: the same four tools, switched with `CODE_SOURCE=github`. The other switches already exist from Step 7h: `--max-workers 1` (one worker against several), `--brain llm|slm`, `--source library|github`. Each improvement round changes one thing (a prompt in `prompts/*.md`, a limit, a tool) and logs the delta against the previous run record.

### Step 11 - Real users and course deliverables
5+ real users who are not classmates; one-page PRD; demo; 10-minute presentation.

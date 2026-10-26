# SpecBridge build steps

What we are building, one step at a time. After each step: report blockers, run its smoke test, and wait for "proceed" before starting the next. Keep this file updated as steps finish or the plan changes. Decisions behind the steps are in [USER_CLARIFICATIONS.md](USER_CLARIFICATIONS.md).

**Product:** a Jira ticket goes in; SpecBridge reads the real code and writes UAT test cases to Confluence. Writing code (plan sections E5 and E7) is out of scope for now.
**Brain:** cloud LLM through OpenRouter (default); local SLM can be switched in later.
**Test code:** 5 OpenMRS 3 frontend repos, frozen at 31 March 2026, in `C:\specbridge-work`.
**New to the project?** Follow [README.md](../README.md) first: it lists the original OpenMRS repo links with their frozen versions, how to clone them (one command: `py -3.12 scripts/setup_workspace.py`), and how to fill in `.env`.

Plan section = section of [autonomous_software_engineering_plan.md](../autonomous_software_engineering_plan.md).

## Status

| Step | What | Plan section | Status |
|---|---|---|---|
| 1 | Pick test repos and real tickets; shortlist golden candidates | E10 (evaluation data) | Done |
| 2 | Download frozen repos; copy 63 tickets into team Jira | E1, E11 (secrets) | Done |
| 3 | Swappable brain: one interface for LLM and SLM | E2 | Built - waiting for OpenRouter key |
| 4 | Code library: index the repos and search them locally | E4 | Planned |
| 5 | Live GitHub code reading (second approach, to compare) | E4 / E5 | Planned |
| 6 | Ticket reader: pull out requirements; flag vague or unsafe tickets | E8-S1 | Planned |
| 7 | Test-case writer: UAT test cases grounded in the code | E6, E8 | Planned |
| 8 | Publish to Confluence and comment on the Jira ticket; simple trigger page | E9, E11, E12 | Planned |
| 9 | Golden answers and scoring: rubric, LLM judge, ship gate | E10 | Planned |
| 10 | Improve over 3+ rounds; compare LLM against SLM | E3, E10 | Planned |
| 11 | Real users (5+, not classmates), one-page PRD, demo, presentation | - | Planned |

Steps 4-11 are the current proposal and may change; each is agreed with the user before it starts.

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

## Planned

### Step 4 - Code library (local)
Split the repos into pieces (components, hooks, functions, routes) with file and repo labels; search them by meaning (local embeddings) and by keywords. **Smoke test idea:** for the golden tickets, do the files that were really changed show up in the top results?

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

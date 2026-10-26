# SpecBridge

A PM writes a Jira ticket; SpecBridge reads the real code and writes UAT test cases (steps and expected results) to Confluence.

- What is being built, step by step: [docs/BUILD_STEPS.md](docs/BUILD_STEPS.md)
- Decisions and open questions: [docs/USER_CLARIFICATIONS.md](docs/USER_CLARIFICATIONS.md)

## What you need

- **Python 3.12.** Only the standard library, except `numpy` for search by meaning (Step 4c).
- **Git 2.30 or newer.**
- **About 100 MB of disk** for the code repos, in a folder that is **not** synced by OneDrive, Dropbox or iCloud.
- **Access to the team's Atlassian site** (`rooks101.atlassian.net`): ask the team to invite you, then create your own API token.
- **An OpenRouter API key** for the AI "brain" (ask the team which key to use).

On Windows use `py -3.12` as shown below. On Mac/Linux use `python3.12` instead.

## Setup

### 1. Get the five code repos SpecBridge is tested on

SpecBridge is tested on five connected OpenMRS 3 frontend repos (React/TypeScript), each **frozen at its version of 31 March 2026**. The golden test tickets were all fixed after that date, so the frozen code is the "before" state. Using any other version gives wrong results.

| Folder name | Original repo | Frozen version (commit) | What it is |
|---|---|---|---|
| `core` | https://github.com/openmrs/openmrs-esm-core | `cf088d5277b12b39022095ce4a9ec9e70e8373e3` | Shared base: app shell, login, navigation, helpers used by every app |
| `patient-chart` | https://github.com/openmrs/openmrs-esm-patient-chart | `8ede2e3a641d470abcd31fe496f5714f2b4fc600` | Patient page: allergies, medicines, vitals, notes, orders, visits |
| `patient-management` | https://github.com/openmrs/openmrs-esm-patient-management | `37d3c1bce6ce05907625761c593077e4eae4613e` | Registration, patient search, appointments, queues, wards |
| `billing-app` | https://github.com/openmrs/openmrs-esm-billing-app | `6a0f80980e71807345ae412fb587bb9d57012bda` | Bills, payments, billable services |
| `dispensing-app` | https://github.com/openmrs/openmrs-esm-dispensing-app | `7f604ab79d7c5120fde2ea1ebdb11241cbd0478c` | Pharmacy: dispensing prescribed medicines |

The same list is kept in [config/repos.json](config/repos.json) and [data/snapshots.json](data/snapshots.json).

**Easiest - one command** (downloads all five and sets each to its frozen version; safe to re-run):

```
py -3.12 scripts/setup_workspace.py --workdir C:/specbridge-work
```

**Or by hand**, for each row of the table (example for `core`):

```
cd C:/specbridge-work
git clone --filter=blob:none --no-checkout https://github.com/openmrs/openmrs-esm-core.git core
cd core
git config core.longpaths true
git checkout -B snapshot cf088d5277b12b39022095ce4a9ec9e70e8373e3
```

Keep the folder names exactly as in the table, and keep each repo's history (do not delete its `.git` folder) - the checks compare against it.

Running an OpenMRS app (`yarn install`, `yarn start`) inside these folders is fine, but `yarn install` changes `yarn.lock`. Put it back afterwards with `git checkout -- yarn.lock` in that repo.

### 2. Fill in your settings

Copy `.env.example` to `.env` in this folder and fill it in. Each line is explained in the file.

```
ATLASSIAN_SITE=https://rooks101.atlassian.net
ATLASSIAN_EMAIL=<your Atlassian email>
ATLASSIAN_API_TOKEN=<from https://id.atlassian.com/manage-profile/security/api-tokens>
JIRA_PROJECT_KEY=SPEC
CONFLUENCE_SPACE_KEY=UAT
BRAIN=llm
OPENROUTER_API_KEY=<your OpenRouter key>
SPECBRIDGE_WORKDIR=C:/specbridge-work
```

`.env` holds secrets. It is git-ignored - **never commit it or paste its contents anywhere.**

### 3. Check that everything works

```
py -3.12 scripts/smoke_test_step1.py --workdir C:/specbridge-work
py -3.12 scripts/smoke_test_step2.py
py -3.12 scripts/smoke_test_step3.py
py -3.12 scripts/smoke_test_step4.py
```

Step 4 builds the code library (`specbridge_index.sqlite`, next to the repos) on first run, in a few seconds. Search by meaning needs `numpy` and a local Ollama with the embedding model: `python3.12 -m venv .venv && .venv/bin/pip install numpy`, install Ollama from https://ollama.com, then `ollama pull nomic-embed-text`; run the Step 4 smoke test and scoring with `.venv/bin/python` (Windows: `.venv\Scripts\python`). To score code search on the golden tickets: `py -3.12 scripts/eval_retrieval.py --method combined` (or `--method hybrid` with embeddings; reports in `data/retrieval/`).

Each writes a report (see [docs/BUILD_STEPS.md](docs/BUILD_STEPS.md) for where) and ends with no `FAIL`. `WARN` lines are known and explained in the report; `PENDING` means a setting in `.env` is still missing.

## Choosing the AI brain

SpecBridge can run on a cloud LLM or, later, a small local model (SLM). Nothing else changes. Settings are in [config/brains.json](config/brains.json).

| Setting in `.env` | Effect |
|---|---|
| `BRAIN=llm` | Cloud model through OpenRouter (default: `google/gemini-3.8-flash`) |
| `BRAIN=slm` | Local model through Ollama (not set up yet) |
| `BRAIN_MODEL=<model id>` | Use another model for a run, e.g. `google/gemini-4-argon`, `anthropic/claude-sonnet-5.5` or any OpenRouter model |

## Folder layout

| Folder | What is in it |
|---|---|
| `specbridge/` | The product code (brain adapter, code library and its agent tools, embedder, search scoring) |
| `scripts/` | Setup, data-building and smoke-test scripts |
| `config/` | Repo list and brain settings |
| `data/` | Frozen versions, golden tickets, smoke-test reports |
| `docs/` | Build steps and decisions |

## Team data already created

These already exist on the team site, so do not re-create them:

- 63 test tickets copied into Jira project `SPEC` (`SPEC-1` to `SPEC-63`). The original OpenMRS ticket for each copy is in [data/golden/jira_import_map.json](data/golden/jira_import_map.json). Re-running `scripts/import_tickets.py` is safe; it does not make duplicates.
- Confluence space `UAT`, where SpecBridge will write its test-case pages.

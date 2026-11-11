# D23 - criterion_worker: a cheap model searches, the main model writes, code checks every citation

- **Status:** Accepted
- **Date:** 2026-11-11
- **Decided by:** the team (Qasim), after the per-ticket cost estimate for multi-turn workers
- **Related:** ARCHITECTURE.md D5 (one code-reading interface), D6 (JSON actions), D7 (cite evidence), D8 (context budget), D9 (limits), D16 / D17 (private workers); [D22](0022-orchestrator-code-proposes-ai-refines.md); `specbridge/agent/worker/` (`criterion_worker.py`, `tools.py`, `evidence.py`), `specbridge/agent/code_source.py`, `prompts/worker_agent.md`, `prompts/write_cases.md`, `config/brains.json` (`roles.worker_agent`), `config/agent.json`

## Context

Each worker reads the real code for its criteria and writes UAT test cases. The search is a loop: every turn the model picks the next tool call and the whole conversation is sent again, so most tokens go into these "what next?" turns, while one final call writes the cases. A cost estimate before building put a typical 2-worker ticket at $0.20-0.30, above the $0.25 cap and the PRD's $0.10 target.

## Decision

1. **Two models per worker** (`config/brains.json`, profile `llm`, `roles.worker_agent`): the search turns use `gemini-3.5-flash-lite` (about $0.30 / $2.50 per million input / output tokens, third-party listings); `write_cases` uses the main model (`gemini-3.8-flash`). `load_brain(role="worker_agent")` picks the role's model; `BRAIN_MODEL` still overrides only the main model.
2. **At most 8 tool calls per worker** (`config/agent.json`, was 12), and the worker's cost share is checked before every turn.
3. **Only code actually read can be cited** (strict D7): `read_file` lines and `grep` match lines become evidence E1, E2, ...; search results and usage lists are pointers only. A case citing anything else, a case for another worker's criterion, an incomplete case, or one that reads like an instruction to an AI is dropped and the drop is recorded.
4. **A separate `write_cases` call** gets only the brief, the criteria and the evidence (up to about 12k tokens of code), and must give at least one happy case and, where it makes sense, a negative or edge case per criterion; criteria it cannot test with the evidence go in `untestable` with the reason, never invented steps.
5. **Tool answers are checked** (`worker/tools.py`): arguments against the tool schemas, answers for their expected keys; any problem goes back to the model as a TOOL ERROR and counts as a turn. One tool cache per run is shared by the workers; each worker has its own library connection (they run in parallel threads).
6. **Context compaction** at 70% of a 15k-token cap: older tool results are cut to their header line, which still names the evidence ids; the newest two stay whole.
7. **Status per worker:** `complete` (every criterion has a case or an untestable reason), `needs_more` (criteria left), `budget_hit` (stopped by the tool-call or cost limit with criteria left), `error` (crashed; the other workers carry on).

## Consequences

- Measured on 2026-11-11 (`data/live_checks/2026-11-11-criterion-worker.md`): SPEC-66 (1 worker, 6 grounded cases) cost $0.057 for the whole ticket in 119 s; SPEC-14 (3 parallel workers) cost $0.10 in 132 s. Both well under the $0.25 cap; the 1-worker ticket is under the PRD's $0.10 target.
- Workers refuse to invent screens: on SPEC-14, whose code (the Angular form engine) is not in the 5 frozen repos, they marked 8 of 9 criteria untestable with reasons.
- A worker can be `complete` with zero cases when all its criteria are untestable; merge, the reviewer and the page must make this visible (nodes 7-9).
- The flash-lite model chooses tools well enough here; if search quality drops on harder tickets, the role can be switched to the main model in `brains.json` without code changes.

## Alternatives considered

- **The main model for every turn:** about 2.5x the input cost for the turns that matter least.
- **12 tool calls:** about 30% more per worker; the live runs finished within 8 (SPEC-66 used 7).
- **Writing the cases in the agent's last turn:** the conversation is long and partly compacted by then; a fresh call with only the evidence is cleaner and easier to check.
- **Allowing citations of the orchestrator's starting pointers:** the worker might cite files it never read, which is what D7 forbids.

# D22 - The orchestrator splits the work in three steps: code proposes, one AI call refines, code checks

- **Status:** Accepted
- **Date:** 2026-11-10
- **Decided by:** the team (Qasim), choosing option (b) after a prototype of a code-only split
- **Related:** ARCHITECTURE.md D9 (limits), D15 (split by acceptance criterion), D16 / D17 (workers see only their slice, never talk to each other), D19 (at most 5 workers + e2e), D8 (context budget); [D20](0020-ground-understand-in-registered-screens.md), [D21](0021-regression-check-for-backend-only-changes.md); `specbridge/agent/nodes/orchestrator.py`, `prompts/orchestrator.md` (`orchestrator-v1`)

## Context

The orchestrator decides which worker (subagent) tests which acceptance criteria. ARCHITECTURE.md planned it as code only. A prototype on real tickets showed the limit of a code-only split, which can only compare the files the search finds for each criterion:

- SPEC-66 (3 criteria about one sorting behaviour): one worker, as it should be.
- SPEC-14 (9 criteria): five workers, four of which would start in the same four files and write overlapping cases, because criteria about the same behaviour ("use lowAbsolute / hiAbsolute", "apply the range before the form is created") found slightly different files. One criterion ("add tests ...") is a developer task, not something a tester can do in a browser; code cannot tell.

Grouping by meaning ("these are all range validation") and spotting non-browser criteria are what a language model is good at; making sure nothing is lost or invented is what code is good at.

## Decision

1. **Code finds the code.** For each usable criterion (status `ok`), the Step 4 search runs on the criterion's own words (plus its quote): hybrid search while Ollama answers, keywords + links otherwise. The top 8 pieces are that criterion's starting evidence, kept as pointers (repo, path, piece, lines, where it appears); workers read the code themselves.
2. **Code proposes groups.** Criteria whose top-3 files share at least 2 files are in the same code area and share a worker; then the two most similar groups are merged until at most `max_workers` (5) remain.
3. **One AI call refines** (`prompts/orchestrator.md`): it gets the criteria, the files each one found, the proposed groups and `max_groups`, and returns the final groups, a one-line focus per worker, and the criteria that cannot be checked in a browser (with the reason). Ticket text stays inside a `<ticket>` data block (D3).
4. **Code checks the answer:** every usable criterion exactly once (in a group or set aside), no invented ids, at most `max_workers` groups, at least one group. A wrong answer or a failed call falls back to the code's proposal and the run goes on; the reason is recorded.
5. **No AI call when there is nothing to split:** one criterion, or a regression check (D21: one worker for the changed screens).
6. **Code decides everything else:** each worker's starting evidence is the union of its criteria's search results (never from the AI; files found for several workers are marked `shared`); the shared brief; each worker's private slice (its criteria and only the ticket lines that quote them, at most about 6k tokens); the budget (cost cap minus what understand and this call spent; 80% split equally among workers with the e2e worker on half a share, 20% kept as reserve; 12 tool calls per worker per round); the e2e worker only with 2+ workers in full scope; conflicting / unclear / non-browser criteria listed in `skipped` with the reason.

## Consequences

- Workers get groups that make sense to a tester, with a stated focus, and do not repeat each other's work; developer-only criteria are set aside openly instead of producing invented browser steps.
- One more AI call per ticket with 2+ criteria (about $0.003 and 10-30 s); none for one criterion or a regression check.
- The plan can differ slightly between runs (the AI part); the code proposal is recorded next to the final groups so they can be compared, and the scoring in Step 9 / 10 can measure whether the refinement helps (worker count, starting files that include the files the real fix changed, test-case coverage).
- Retry rounds (the reviewer sending weak criteria back) are built with the reviewer, node 8.

## Alternatives considered

- **Code only:** free and repeatable, but splits by files rather than meaning (SPEC-14 above) and cannot tell developer tasks from browser checks.
- **The AI decides alone:** could drop or invent criteria, and is not grounded in the code unless given the search results; we give it those and still check its answer.
- **One worker per criterion, no grouping:** simplest, but repeats the same code reading many times and produces overlapping test cases.

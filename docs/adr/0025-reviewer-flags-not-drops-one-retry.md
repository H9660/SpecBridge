# D25 - reviewer: code checks flag (never drop), one independent AI review call per criterion in parallel, one retry round for weak criteria

- **Status:** Accepted
- **Date:** 2026-11-11
- **Decided by:** the team (Qasim)
- **Related:** ARCHITECTURE.md D2, D3, D7, D9 (limits: 2 rounds), D18 (reserve); [D21](0021-regression-check-for-backend-only-changes.md), [D22](0022-orchestrator-code-proposes-ai-refines.md), [D23](0023-criterion-worker-design.md), [D24](0024-merge-code-builds-ai-only-removes-renames.md); `specbridge/agent/nodes/reviewer.py`, `prompts/reviewer.md` (`reviewer-v3`), `orchestrator.retry_plan`, `merge.combine_rounds`, `config/brains.json` (`roles.reviewer`)

## Context

The merged plan goes to a product manager, so it needs a quality gate: are all criteria covered, is every case supported by the code it cites, is it safe to publish? The live runs showed why: workers sometimes read little before writing (SPEC-12), and on another ticket every criterion of a worker was untestable. ARCHITECTURE.md planned code checks, an independent AI review "ideally from a different model family", and retries for weak criteria (at most 2 rounds).

## Decision

1. **Code checks never drop a case; they flag it** ("may be ambiguous, please check"): cites evidence not in the plan; cited file or lines not at the frozen version (code files from the library, other files such as `translations/en.json` from the frozen checkout); quoted labels not found in the cited code, the code's on-screen text or the ticket; only test files cited; text that reads like an instruction to an AI. Secrets are still redacted (the text changes, nothing is removed). Per criterion: no case and no reason (coverage), or no negative / edge case.
2. **One independent AI review call per criterion, all in parallel** ("plan B", chosen by the user on 2026-11-11 after first building one call per plan; role `reviewer` in `config/brains.json`; `gemini-3.6-flash` for now, the user's choice while 3.8-flash was overloaded). Each call is a fresh context with one criterion (and the ticket's words for it), its cases including flows through it, only the code those cases cite, re-read from the library (up to 150 lines per evidence entry), and the code flags - never the workers' reasoning, the full ticket or the other criteria. At most `max_concurrency` (5) calls run at once; they are plain calls inside the node, not subagents. Each returns `ok` / `weak`, problems (coverage, grounding, clarity, missing-negative, unsafe) and a retry hint. Only the verdict for the call's own criterion is used; a reply without it is asked once more, and if it fails again (or the call errors) that criterion keeps the code checks' verdict and the final reason names it. The cited code is the version before the ticket is done, so for a criterion that asks for a change, the old behaviour in the code is expected: a case is grounded when it cites the place where the change goes and expects what the criterion asks for (prompt `reviewer-v3`). The reviewer only judges; it changes nothing (D2).
3. **Verdicts:** a criterion is weak if it has no case and no reason, or the AI says weak. Untestable (with a worker's reason) and skipped criteria pass through and are never retried.
4. **One retry round** (round 1 only, and only if the cost and time caps allow): the reviewer sends the weak criteria back to the orchestrator, which plans one worker per round-1 group of weak criteria with the reviewer's problems and hint in the slice, the code cited in round 1 as starting pointers, 90% of the remaining budget (10% kept for the second review), no AI grouping and no e2e worker. Merge then lets round-2 cases replace a criterion's round-1 cases only if round 2 produced some (a retry never makes a criterion worse). The second review only re-judges the retried criteria; the others keep their verdicts. After round 2 the review is final.
5. **Final status:** `complete` if no criterion is weak, otherwise `incomplete` with the reason ("AC1 still weak (max_rounds)"); if the AI review call failed, the reason says the verdicts come from the code checks only.

## Consequences

- Measured on SPEC-12's real plan (`data/live_checks/2026-11-11-reviewer.md`). One call per plan (first build): all 6 criteria ok, $0.020. One call per criterion (plan B): **all 6 weak**, $0.052, 6 calls, 17-108 s. Plan B is right about the main problem: every case cites only the form wrapper (`conditions-form.workspace.tsx`, which just renders `ConditionsWidget`), and no worker read the widget where the search and keys live. The single call had missed that. With one planted ungrounded case, plan B named exactly that case in AC5.
- Plan B costs about 2.5x per review, and a stricter review sends more criteria to the retry round, which costs more.
- `reviewer-v2` also marked AC4 weak because the code always shows 'Record condition', although the criterion asks for 'Edit condition' when editing - a change no retry can find code for. `reviewer-v3` says the old behaviour is expected for a requested change: AC4 became ok, and AC6 lost its two title problems but kept its real one (keyboard handling not in the cited code). The other four stay weak for citing the wrapper. $0.057.
- Nothing a worker wrote is silently lost; the page shows flags and weak criteria for a person to judge.
- A retry costs roughly one worker per weak criterion group plus a smaller second review, paid from the reserve.
- The reviewer uses the same model family as the writers, so they can share blind spots; the role can be switched in `brains.json` and compared in Step 9 / 10.

## Alternatives considered

- **Dropping cases that fail hard checks** (first proposal): rejected by the user - flag them and let a person decide.
- **One AI call for the whole plan, split only when too big** (built first, recommended for cost): about 2.5x cheaper and it can see one case serving two criteria, but on SPEC-12 it passed cases that the per-criterion calls showed were not grounded. Replaced by plan B at the user's request.
- **A stronger model (`gemini-4-argon`) or the cheap `flash-lite`:** the reviewer's judgement matters, but the main-class model was judged enough; flash-lite reads code less carefully.
- **More than one retry round:** more cost and time for diminishing returns; ARCHITECTURE.md D9 sets 2 rounds.

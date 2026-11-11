# Architecture decision records (ADRs)

One file per significant design decision: what was decided, why, what it costs, and what was rejected. A decision is recorded when it changes how the agent works, or would surprise someone reading the code.

- **Numbering** continues the decisions D1-D19 in [ARCHITECTURE.md section 2](../ARCHITECTURE.md#2-key-decisions), which stay there. New decisions start at D20 and get a file here: `NNNN-short-title.md`.
- **Status:** Proposed, Accepted, Superseded by DNN, or Rejected. An accepted ADR is not rewritten; a change of mind is a new ADR that supersedes it.
- **Who decided** is recorded, along with the date. Day-to-day questions and answers stay in [USER_CLARIFICATIONS.md](../USER_CLARIFICATIONS.md); an ADR links to the rows it came from.

| ADR | Title | Status | Date |
|---|---|---|---|
| [D20](0020-ground-understand-in-registered-screens.md) | `understand` is given the real screens from the code, picked per ticket at run time | Accepted | 2026-11-09 |
| [D21](0021-regression-check-for-backend-only-changes.md) | Backend-only changes to a real screen get a regression check; other untestable tickets go to clarify (future: re-run from `understand` when the PM answers in Jira) | Accepted (re-run part: future) | 2026-11-09 |
| [D22](0022-orchestrator-code-proposes-ai-refines.md) | The orchestrator splits the work in three steps: code proposes, one AI call refines, code checks | Accepted | 2026-11-10 |
| [D23](0023-criterion-worker-design.md) | criterion_worker: a cheap model searches, the main model writes, code checks every citation | Accepted | 2026-11-11 |
| [D24](0024-merge-code-builds-ai-only-removes-renames.md) | merge: code builds the plan; the AI may only suggest removing duplicates and renaming, and code checks every suggestion | Accepted | 2026-11-11 |

## Template

```markdown
# DNN - Title

- **Status:** Proposed | Accepted | Superseded by DNN | Rejected
- **Date:** YYYY-MM-DD
- **Decided by:** ...
- **Related:** ARCHITECTURE.md Dx, USER_CLARIFICATIONS.md (date), code files

## Context
What problem, with evidence.

## Decision
What we do, precisely enough to check the code against it.

## Consequences
What gets better, what it costs, what new risks it brings.

## Alternatives considered
Each option and why it was not chosen.
```

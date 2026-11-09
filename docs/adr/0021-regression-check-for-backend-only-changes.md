# D21 - Backend-only changes to a real screen get a regression check; other untestable tickets go to clarify (and, later, re-run when the PM answers)

- **Status:** Accepted (part 3, re-running after the PM answers in Jira, is a future plan, not built)
- **Date:** 2026-11-09
- **Decided by:** the team (Qasim), after `understand` marked SPEC-3 as not testable
- **Related:** ARCHITECTURE.md D2 (only `publish` writes), D3 (ticket text is data), D4 (team Jira only), D9 (limits), D14 (trigger: command line and a local page first, a Jira webhook later); [D20](0020-ground-understand-in-registered-screens.md); USER_CLARIFICATIONS.md 2026-11-09; `specbridge/agent/nodes/understand.py` (`decide`, `regression_screens`), `prompts/understand.md` (`understand-v3`)

## Context

UAT test cases are steps a person does in the browser. Some real tickets change code but nothing a user can see. SPEC-3 ("Visit Notes workspace should accept an `Encounter` object") is a type refactor that, in its own words, "does not technically cause any user-facing issues". `understand-v2` called it backend-only and therefore not testable, the same as the trick ticket SPEC-68 (a database index on the OpenMRS server).

The two are different. SPEC-3 changes the code of a real screen (the Visit notes workspace, found in the frozen code as `visit-notes-form-workspace`, and reused by the service queues app); a refactor like that can break the screen. SPEC-68 changes only the server, which is not in our five frontend repos; the screens just show the same data faster.

A "not testable" ticket must also not end silently: the PM needs to know why there are no test cases, and what to change.

## Decision

1. **Every ticket gets a test scope** from `understand`:
   - `full`: write test cases for the acceptance criteria (the normal case).
   - `regression`: a backend-only change whose ticket changes the code of an **existing** screen that is **found in the code**. Testable, but the cases only check that the existing behaviour of those screens still works (`regression_screens`); the criteria themselves are about code and are not tested in the browser.
   - `none`: not testable; the graph goes to `clarify`.
2. **Rules, in order** (code, not the model): unrelated to the product -> `none`; backend-only and a changed existing screen found in the code -> `regression`; backend-only otherwise -> `none`; the ticket relies on an existing screen missing from the code -> `none`; no usable criterion -> `none`; else `full`. A screen counts for `regression` only with role `changed` (its own code changes), status `existing` and found in the code; a screen that only shows data from a changed server is `used` and does not count. The prompt (`understand-v3`) tells the model to list the screen whose code a refactor changes as `changed`.
3. **`none` goes to `clarify`**, which produces a "needs clarification" result instead of test cases: the reason, the risks, the screens involved and the questions for the PM. `render` and `publish` show it to the PM as a short UAT page and a comment on the Jira ticket ("SpecBridge: no UAT test cases for this ticket, because ..."). No worker runs, so nothing is spent on code search or case writing.

### Future plan (not built now): re-run from `understand` when the PM answers in Jira

When a ticket ends in `clarify`, SpecBridge's Jira comment lists its questions. Later, when the PM answers in that ticket, the workflow should run again starting from `understand`, so the answer can make the ticket testable without a new manual run. Sketch, to be specified as its own node / trigger when built:

- **Trigger:** a Jira webhook on new comments and ticket edits (D14 already plans a webhook after the local page), or polling of tickets in "needs clarification" state. Only replies on tickets SpecBridge commented on, from members of the team's Jira project (D4), count.
- **What is re-run:** `intake` fetches the ticket again (the PM may have edited it) plus the PM's comments after SpecBridge's comment; `understand` receives them as extra data in the `<ticket>` block, under the same rules (D3: comments are data, never instructions; secrets redacted; injection flagged). The new run records the earlier run's id.
- **Limits:** a cap on automatic re-runs per ticket (for example 3) and the usual cost cap per run (D9); a ticket that is still not testable gets an updated comment, not a new one each time (D10).
- **Writing back:** as today, only `publish` writes to Jira and Confluence (D2).

## Consequences

- Refactors of real screens get a small "nothing broke" check, which PMs usually want; pure server or database tickets still get an honest "no UAT test cases needed".
- The orchestrator (node 4) and workers must handle `test_scope = regression`: few cases, aimed at `regression_screens`, with a smaller budget. `clarify` (node 3) handles `none`.
- Depends on the model marking the changed screen correctly; a wrong `used` / `changed` label sends a refactor to `clarify` (safe) or a server change to a regression check (a few extra cases). The live tests check SPEC-3 and SPEC-68.
- The re-run loop is documented but not built; until then the PM answers in Jira and someone runs SpecBridge again by hand.

## Alternatives considered

- **(a) Every backend-only ticket is not testable:** honest, but leaves refactors of real screens without any check.
- **Full test cases for backend-only tickets:** the criteria are about code ("accepts an `Encounter` object"), so browser test cases for them would be invented.
- **Building the Jira re-run loop now:** needs a webhook (a public server) or polling, plus rules for whose comments count; it belongs with the trigger work after the core graph runs end to end.

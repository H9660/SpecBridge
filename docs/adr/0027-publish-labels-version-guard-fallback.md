# D27 - publish: find the page by labels, never overwrite a person's edit, one Jira comment, save locally on failure

- **Status:** Accepted
- **Date:** 2026-11-11
- **Decided by:** the team (Qasim): "complete next node" - the recommended choices below
- **Related:** ARCHITECTURE.md D2 (only plain code writes), D4 (only the team's site and project), D10 (re-runs update the page; human edits are never overwritten); [D26](0026-render-one-document-three-formats.md); `specbridge/agent/nodes/publish.py`, `specbridge/atlassian.py`, `specbridge/agent/preflight.py` (`check_atlassian`)

## Context

In live mode the page `render` made has to reach Confluence, and the ticket needs a comment that links to it. This is the only node that writes outside this machine, so it must be safe to run twice, must not destroy a product manager's edits, and must never lose the work when Atlassian is down. The token in `.env` is a person's own token (a bot account is still open, step 8d).

## Decision

1. **Checks before any write** (nothing is written if one fails): live mode; the Atlassian settings are set; the ticket is in the configured Jira project and on the configured site; there is a page; it is well-formed XML and under 2 MB; the page, its title and the comment hold no secret-like text. START also checks the settings and that the Confluence space can be read, in live mode, before any AI call.
2. **Finding the page:** by its labels (the ticket key + `specbridge`) in the space, else by its exact title. Labels survive a change of the ticket's title. The space key Confluence reports is used for the search and the page address (the configured `UAT` turned out to be an old alias of the real key `SU`).
3. **New page:** created with the labels (`spec-66`, `specbridge`, `awaiting-pm-review`) and a page property `specbridge` = {page_version, run_id}.
4. **Existing page (D10):** updated only if SpecBridge wrote its current version - the version number in the property matches, or the current version's message starts with `[SpecBridge]` (this covers a crash between the update and the property). Otherwise a person edited it: the page is left alone and the new draft is added as a comment on the page, with a note.
5. **Jira:** one comment per ticket. It is this account's comment starting with `[SpecBridge]`, updated on re-runs, else created. `{page_url}` is filled in and shown as a link. Comments by other accounts are never touched.
6. **Failures** (Atlassian errors, network, timeouts) never crash the run: `state["published"]` and the run note say what failed, the command exits with 1, and the page is saved locally as `save_local` would.

## Consequences

- Re-running a ticket is safe: same page, same comment, a new page version each time.
- A product manager's edits are never overwritten; they see the new draft as a page comment.
- If the page was updated but the comment failed, the result says so and keeps the page address.
- Until the bot account exists, everything is written under the token owner's name (on 2026-11-11 the token in `.env` belonged to Hussain Lohawala).
- Checked live on 2026-11-11 (`data/live_checks/2026-11-11-publish.md`): SPEC-66 created the page and one Jira comment, and a second run updated both (page version 2, still one comment). A person's edit between runs is covered by the offline tests only.

## Alternatives considered

- **Find the page by title only:** a renamed ticket would create a second page.
- **Compare authors to detect a person's edit:** does not work while SpecBridge writes with a person's own token.
- **Always overwrite, or always create a new page:** rejected in ARCHITECTURE.md D10.
- **Fail the run when publishing fails:** the cases were already paid for; saving them locally and reporting the error keeps the work.

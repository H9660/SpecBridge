# D26 - render: one document written three ways (Confluence, HTML, Markdown), a page for every finished run

- **Status:** Accepted
- **Date:** 2026-11-11
- **Decided by:** the team (Qasim)
- **Related:** ARCHITECTURE.md D2, D3, D10, §3 (`render`); [D25](0025-reviewer-flags-not-drops-one-retry.md); `specbridge/agent/nodes/render.py` (`render-v1`), `specbridge/agent/graph.py`, `specbridge/agent/run_record.py`

## Context

The reviewed plan has to reach a product manager as a Confluence page, and the ticket needs a short comment that links to it. Dry-run and eval mode need the same page as local files. ARCHITECTURE.md listed the page's contents (summary, screens, cases grouped by criterion with blank Actual result and Pass/Fail, open questions, the review report, evidence, run details). Every input is untrusted text from the ticket or the AI.

## Decision

1. **Code only, no AI, no network.** `render` builds one document (a list of blocks) and writes it three ways: Confluence **storage format** (for `publish`), a standalone **HTML** page and a **Markdown** copy (both for `save_local`; the Markdown copy was the user's request). It also writes the plain-text **Jira comment** with the `[SpecBridge]` marker and a `{page_url}` placeholder.
2. **Every finished run gets a page.** The graph now goes reviewer (final) -> render, clarify -> render, and orchestrator (nothing to send or incomplete) -> render. There are three kinds of page: a test plan, a questions-only page for clarification (its comment is the one `clarify` wrote), and a short page with the reason when no test case was written.
3. **Layout** (the user's choices; the recommended ones where not stated):
   - test cases grouped by criterion in **6 columns**: ID (with type, title and the cited EV ids), Preconditions, Steps, Expected result, Actual result (blank), Pass/Fail (blank)
   - the reviewer's flags in a full-width row under their case ("May be ambiguous, please check")
   - each criterion has a status tag (OK, NEEDS ATTENTION, UNTESTABLE, SKIPPED, NO TEST CASES); a weak criterion shows the reviewer's problems and "what is missing", and its cases are kept
   - end-to-end flows in their own section, with "also tested in flow TC-xx" under each criterion they cover; a case shared by two criteria appears once
   - evidence as GitHub links to the cited lines at the frozen commit, without code
   - the workers' notes, and what they could not find, in a collapsed section
4. **Safety (D3):** all text from the ticket, the AI and the code has secrets redacted again and is escaped, so it can never become markup or a Confluence macro. Questions and notes that read like instructions to an AI are left out.
5. **Deterministic:** the same state and clock give the same output, byte for byte. Internal stop codes are shown in words ("after the retry round").
6. **Run record:** keeps the page's title, labels, storage, comment and summary, but not the HTML and Markdown copies, which `save_local` writes as files.

## Consequences

- Measured (`data/live_checks/2026-11-11-render.md`): SPEC-12's real plan with a real review renders in about 20 ms to a 30 KB page; SPEC-64's real clarification record renders to a questions-only page. Rendering costs $0.
- The page shows weak criteria and flagged cases openly, so a PM sees what to check instead of a silently shortened plan.
- `publish` (node 11) can send `storage` as is; only `{page_url}` in the comment needs filling in.
- The storage format uses four Confluence macros (status, expand, tip/note/warning/info panels); the HTML and Markdown copies replace them with plain equivalents.

## Alternatives considered

- **Three separate builders, one per format:** more code, and the formats would drift apart.
- **Letting the AI write the page:** costs money and breaks D2 / D3; the page is a fixed layout of data we already have.
- **8 columns (separate Type and Evidence):** too wide on a laptop; the user chose 6.
- **Code excerpts on the page:** long pages; the GitHub links show the exact lines at the frozen commit.

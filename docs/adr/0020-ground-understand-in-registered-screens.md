# D20 - `understand` is given the real screens from the code, picked per ticket at run time

- **Status:** Accepted
- **Date:** 2026-11-09
- **Decided by:** the team (Qasim), after the first 43-ticket run of `understand`
- **Related:** ARCHITECTURE.md D3 (ticket and code text are data), D5 (one code-reading interface), D8 (context budget); USER_CLARIFICATIONS.md 2026-11-09; `specbridge/agent/nodes/understand.py`, `prompts/understand.md` (`understand-v2`), `specbridge/code_index.py` (`screens_for`, `find_screen`)

## Context

`understand` is one AI call that reads the cleaned ticket and decides whether test cases can be written. In its first version (`understand-v1`) the model saw only the ticket and a six-line description of OpenMRS. It knew nothing about the code, so it could not tell:

- a change to a screen that **exists** ("sort allergies on the Allergies widget"),
- a **new** screen or button the ticket asks to build ("add a Request Refund action"), and
- a screen the ticket **assumes exists but does not** (the trick ticket SPEC-64's "Dental Chart tab").

After the answer, code looked each screen name up in the code library, and any screen the ticket changes that was not found made the ticket "not testable". On the first 43 real tickets this blocked 3 tickets wrongly: SPEC-32 ("Request Refund") and SPEC-39 ("verification page") ask for new screens, which by definition are not in the frozen code; SPEC-14 named a technology ("Angular form engine") as if it were a screen.

The repos themselves are the ground truth about what exists. The code library (Step 4) already knows every screen each app registers in its `routes.json`: 297 entries (184 widgets, 40 workspaces, 59 modals, 14 pages), about 3,700 tokens as a list.

## Decision

1. **Ground truth goes into the prompt, picked per ticket.** Before the AI call, code runs the Step 4 keyword search (plus links, no embedder) with the ticket's text and takes the 25 registered screens of the best-matching files (`CodeIndex.screens_for`). They are added to the user message as "Screens registered in the code that look related to this ticket (from the real code - ground truth about what exists, but only the closest matches)". About 300-500 tokens.
2. **Generated at run time, never written into the prompt file.** `prompts/understand.md` holds only fixed instructions. The list, like the OpenMRS description (from `config/repos.json`), is built each run from the code library, which rebuilds itself when a repo's frozen commit changes. When the code changes, no prompt is edited.
3. **The model labels each screen it lists:** `status` = `existing` (the ticket talks about it as already there) or `new` (the ticket asks for it to be built), and `matches` = the exact registered name from the list when it is one of them. Only things a user sees count as screens, not libraries, engines or APIs.
4. **Code decides what exists, the model only reads the wording.** A screen counts as found when its `matches` is one of the names actually shown (a made-up name is ignored) or the code library finds its name (`find_screen`: missing only if one of its words appears nowhere in the code). The model's own "unknown-screen" guess is dropped whenever the library was checked.
5. **A ticket is blocked only on strong evidence:** a screen the ticket treats as `existing`, that it changes, and that is found neither in the list nor by the library. A `new` screen that is missing is expected and never blocks. A `new` screen that matches a registered one adds a question ("is this a change to the existing one?").

## Consequences

- New-feature tickets are no longer stopped; the fake-screen trick ticket still is. The model also maps the ticket's words to real names ("sign-in page" -> `login`), which later nodes can use.
- About 300-500 more input tokens per ticket (about $0.0003 at list price); no extra AI call; the search takes about 0.1 s and needs no Ollama.
- Still not perfect: the shortlist can miss the right screen (the library lookup is the backstop), the model can mislabel `existing` / `new` on ambiguous wording, and a ticket asking for something that already exists is only flagged when the model matches it. Deeper checks against the code stay with the workers, who read the code, and the reviewer, who rejects cases citing screens not in the code.
- Fits the small local model (SLM) later: a 25-screen shortlist fits its context; the full list would not.

## Alternatives considered

- **The model alone (v1):** cannot know what exists; blocked real new-feature tickets.
- **The full list of all 297 screens in every prompt:** about 3,700 tokens, mostly irrelevant to the ticket, too big for the SLM.
- **Writing the screen list into `prompts/understand.md`:** goes stale as soon as the code changes and must be edited by hand.
- **Dropping the screen check from `understand`:** fake-screen tickets would reach the workers and cost a full run before being caught.

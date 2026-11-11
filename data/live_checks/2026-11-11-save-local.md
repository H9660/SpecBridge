# Live check: save_local (node 10) - the first full run through every node - 2026-11-11

`.venv/bin/python scripts/run_ticket.py SPEC-66 --mode dry-run`: START -> intake -> understand -> orchestrator -> criterion_worker -> merge -> reviewer -> render -> save_local. The saved files are copied to [2026-11-11-save-local/](2026-11-11-save-local/) for review (the run folder itself is in the git-ignored `data/runs/`). Open [page.html](2026-11-11-save-local/page.html) in a browser.

| | Result |
|---|---|
| Status | `complete`: 3 criteria, all ok; 6 test cases (1 worker, 5 tool calls, 5 pieces of code read); 1 open question |
| Files | `data/runs/SPEC-66/20261111-212317-4d465c/` next to `20261111-212317-4d465c.json`: page.html 13.7 KB, page.md 9.2 KB, page.storage.xml 12.6 KB, comment.txt; no warnings, no error |
| Cost | $0.073 (57k tokens, estimated at list prices) |
| Time in the nodes | 97 s: understand 9 s, orchestrator 7 s, worker 59 s, reviewer 21 s, render 0.01 s, save_local 0.03 s |
| Models | main `gemini-3.6-flash` (see below), worker search `gemini-3.5-flash-lite`, reviewer `gemini-3.6-flash` |

**`gemini-3.8-flash` was hanging at Google.** The first try stopped in `understand` after 590 s without an answer, and a one-word test call to 3.8-flash got no answer in 100 s, while 3.6-flash answered in 2 s. The run was resumed from its checkpoint (`--resume --run-id 20261111-212317-4d465c`) with `BRAIN_MODEL=gemini-3.6-flash`, which changes only the main model. The record's wall time (821 s) includes the 590 s wait.

Fixed after the run:
- The files were private (`-rw-------`, from Python's temporary-file helper). They now get normal permissions (`-rw-rw-r--` here).
- The comment said "1 open questions". Now "1 open question" (and "1 case is flagged").

Found, for node 5 (not changed yet):
- The worker gave TC-06 the type `empty-state`, which is not one of happy / negative / edge. So the reviewer's code check did not count it as an edge case and flagged AC3 "no negative or edge case", although TC-06 is one. The worker's case schema should allow only the known types (or map others to `edge`).

The comment as saved (before the plural fix):

```
[SpecBridge] SPEC-66: UAT test cases ready for PM review
6 test cases for 3 acceptance criteria (3 ok).
1 open questions.
Page: {page_url}
```

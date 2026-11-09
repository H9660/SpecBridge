# understand on the SPEC tickets - prompt understand-v2 (2026-11-09)

Run 2026-11-09 11:50; model gemini-3.8-flash.

| Group | Tickets | As expected |
|---|---|---|
| real | 5 | 1 |
| trick | 2 | 0 |

Total cost $0.032; time per ticket 109.1-1143.0 s (median 645.2 s).

| Ticket | Group | OK | Testable | Domain | Criteria (stated / inferred) | Questions | Risks | Problems |
|---|---|---|---|---|---|---|---|---|
| SPEC-3 | real | **no** | False | fits | 1 (1 / 0) | 1 | backend-only | testable False (expected True): backend-only change: nothing a user can check in the browser, so UAT test cases do not apply |
| SPEC-14 | real | **no** | - | - | - | - | - | UnderstandError: the AI could not answer: google returned 503 after 6 tries: UNAVAILABLE: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later. |
| SPEC-32 | real | yes | True | fits | 9 (1 / 8) | 3 | contradictory | - |
| SPEC-35 | real | **no** | False | fits | 1 (0 / 1) | 2 | vague | testable False (expected True): no checkable acceptance criteria could be found or inferred |
| SPEC-39 | real | **no** | - | - | - | - | - | UnderstandError: the AI could not answer: cannot reach google at https://generativelanguage.googleapis.com/v1beta/openai: The read operation timed out |
| SPEC-64 | trick (ADV-1) | **no** | - | - | - | - | - | UnderstandError: the AI could not answer: cannot reach google at https://generativelanguage.googleapis.com/v1beta/openai: The read operation timed out |
| SPEC-66 | trick (ADV-3) | **no** | - | - | - | - | - | UnderstandError: the AI could not answer: cannot reach google at https://generativelanguage.googleapis.com/v1beta/openai: The read operation timed out |

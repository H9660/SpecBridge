# Live check: the Jira trigger service (step 8e) on this machine - 2026-11-12

The real service (`specbridge/service.py`) on a free local port with real HTTP requests, the real agent in live mode and the real Jira and Confluence; only the Jira Automation rule and the tunnel were left out (they need the user). The webhook secret was a temporary one, kept in memory only (not `.env`).

| Step | Result |
|---|---|
| `POST /run` with a wrong secret | **401** `missing or wrong secret`; nothing queued, nothing written |
| `POST /run {"key": "SPEC-66"}` with the secret | **202** `{"queued": true, "position": 1}`, answered in 2.2 s (the ticket's comment is updated before the answer) |
| The ticket's comment 4 s later | "[SpecBridge] SPEC-66: Generating UAT test cases for PM and engineering review / SpecBridge is reading the ticket and the code. This usually takes 2-5 minutes; ..." |
| The same request again while running (a double click) | **200** `SPEC-66 is already queued or running`; no second run |
| The run | `complete` after 105 s, $0.072; the page <https://rooks101.atlassian.net/wiki/spaces/SU/pages/5111809> went to version 3 (`[SpecBridge] run 20261112-013436-63c1fb`) |
| The ticket's comment after the run | the same single comment, now "UAT test cases ready for PM review / 6 test cases for 3 acceptance criteria (3 ok). 1 case is flagged "may be ambiguous". / Page: <link>" |
| The same request right after | **429** `SPEC-66 ran recently; try again in 10 min` |
| The day's spending (`data/service/ledger.json`) | $0.0716, 1 run |

The log (`data/service/service.log`) had the caller's address, the path, the status, ticket keys and outcomes - no secret and no headers.

Still to do with the user: put the secret in `.env`, install `cloudflared`, start `scripts/serve.py` and the tunnel, create the Jira rule, and press **Run SpecBridge** on a ticket (`docs/DEPLOY_JIRA.md`).

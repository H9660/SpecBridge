# D28 - A "Run SpecBridge" button in Jira: an Automation rule calls a small local service through a tunnel

- **Status:** Accepted
- **Date:** 2026-11-12
- **Decided by:** the team (Qasim): option B (button + webhook) over polling and a Forge app; the recommended settings
- **Related:** ARCHITECTURE.md D2, D4, D9, D14 (command line and local page first, webhook later); [D27](0027-publish-labels-version-guard-fallback.md); `specbridge/service.py`, `scripts/serve.py`, `docs/DEPLOY_JIRA.md`

## Context

So far only a person at the command line could start a run. Product managers work in Jira, so the run should start from the ticket. SpecBridge cannot run inside Atlassian: it needs Python, the frozen repos, the code index and Ollama on one machine. Three options were compared: a poller that looks for a label (no public address), a Jira Automation rule that calls a web service (a button, but needs a public HTTPS address), and a Forge app (runs JavaScript on Atlassian's servers and would still have to call our machine).

## Decision

1. **Jira side:** one Automation rule in project SPEC with a *manual trigger* ("Run SpecBridge" in the ticket's Actions menu) and a *Send web request* action: `POST /run` with `{"key": "{{issue.key}}"}` and the header `X-SpecBridge-Secret`. No code in Jira; other triggers (a status change, a label) can be added later in the same rule.
2. **Our side:** `scripts/serve.py` starts `specbridge/service.py`, standard library only, listening on `127.0.0.1:8765`. A Cloudflare quick tunnel gives it a public HTTPS address for the demo.
3. **Checks on every request:** path and method; the secret, at least 24 characters, compared in constant time and checked before the body is read; a JSON body of at most 4 KB; a ticket key of the configured project. Then: not already queued or running (a double click runs once), not run in the last 10 minutes, the queue (20) not full, and the day's spending under `daily_budget_usd` ($2.00). Queued and running tickets count at their $0.25 cap, so the day can never go over.
4. **One run at a time,** in a worker thread, with `run_ticket(key, "live")`. The page and the result comment are written by the publish node exactly as from the command line.
5. **The ticket's one `[SpecBridge]` comment** says "Generating UAT test cases for PM and engineering review" at once (wording asked for by the user), is replaced by publish's result, and says so if the run failed (a short, redacted reason) or the daily limit stopped it. This is the only thing the service writes. It is a deliberate, narrow addition to D2: plain code, the ticket that was asked for, the same marker comment.
6. **State in `data/service/`** (git-ignored): the queue (a restart picks it up, and a run that was interrupted is queued again), the day's spending, and a log with ticket keys and outcomes but never the secret or request headers. `--dry-run` runs the same service without writing anything to Jira.

## Consequences

- A PM gets test cases from the ticket itself in a few minutes, and sees progress in the comment straight away.
- The machine and the tunnel must stay up; a quick tunnel's address changes on every restart, so the rule's URL must then be updated (a named tunnel or a VM fixes this).
- Everything is still written with the token in `.env` (a person's, until the bot account in step 8d).
- Cost is bounded per ticket ($0.25) and per day ($2.00 by default).

## Alternatives considered

- **Polling for a label:** no public address needed, but a delay of up to a few minutes and no button. Kept as a fallback if a public address is not possible.
- **A Forge app:** cannot host our Python, the index or Ollama, so it would be this design plus an app to maintain.
- **Running every request at once in parallel:** more Gemini rate-limit errors and no clear cost bound; one at a time is enough for a team.

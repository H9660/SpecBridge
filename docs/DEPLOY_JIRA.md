# Deploy: the "Run SpecBridge" button in Jira

This adds a **Run SpecBridge** button to every ticket in the `SPEC` project. A product manager presses it, and a few minutes later the ticket has a UAT page in Confluence and one `[SpecBridge]` comment linking to it. Design: [ADR D28](adr/0028-jira-button-webhook-service.md).

```
Jira ticket → Actions → "Run SpecBridge"           (a Jira Automation rule)
   → POST https://<public address>/run  {"key": "SPEC-66"}  + secret header
   → tunnel → SpecBridge service on our machine (scripts/serve.py, 127.0.0.1:8765)
   → one run at a time, live mode → Confluence page + the ticket's [SpecBridge] comment
```

## What the product manager sees

| When | The ticket's `[SpecBridge]` comment |
|---|---|
| Right after pressing the button | "Generating UAT test cases for PM and engineering review ... this usually takes 2-5 minutes" (plus "Queued behind N other tickets" if others are waiting) |
| When the run is done | "UAT test cases ready for PM review" (or "some need attention", or "needs clarification"), with the page link |
| If the run failed | "UAT test cases could not be generated this time", the reason, and "try again later" |
| If today's limit is used up | "Not started - the daily SpecBridge limit is reached" |

It is always the same single comment, updated in place.

## 1. What the machine needs

The service runs on a machine that stays on while people use the button (a team PC, a lab machine or a small VM). It needs the same setup as the command line:

| Needed | Check |
|---|---|
| This repo, with `.venv` installed | `.venv/bin/python -m pytest tests -m "not live"` passes |
| `.env` with `GEMINI_API_KEY` and the Atlassian settings | `.venv/bin/python scripts/run_ticket.py SPEC-66` works |
| The frozen repos and the code index in `SPECBRIDGE_WORKDIR` | the same run finds code |
| Ollama with `nomic-embed-text` running | `curl http://127.0.0.1:11434/api/tags` (without it, code search uses keywords only) |

## 2. Make the secret

The Jira rule proves it is Jira by sending a secret that only the rule and the service know.

```bash
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Put the result in `.env`:

```
SPECBRIDGE_WEBHOOK_SECRET=<the string you just made>
```

Never commit it and never paste it in chat. If it leaks, make a new one and update the `.env` file and the Jira rule.

## 3. Try the service without Jira (dry-run)

```bash
.venv/bin/python scripts/serve.py --dry-run
```

In a second terminal (put your secret in place of `<secret>`):

```bash
curl -s localhost:8765/health
curl -s -X POST localhost:8765/run -H "Content-Type: application/json" \
     -H "X-SpecBridge-Secret: <secret>" -d '{"key": "SPEC-66"}'
```

You should get `{"ok": true}`, then `{"queued": true, "position": 1}`. In dry-run the page is saved under `data/runs/SPEC-66/<run_id>/` and nothing is written to Jira. Stop the service with Ctrl-C.

## 4. Start it for real

```bash
.venv/bin/python scripts/serve.py
```

It checks Gemini and the Confluence space first, and refuses to start if something is wrong. It listens only on this machine (`127.0.0.1:8765`).

## 5. Give it a public address (Cloudflare quick tunnel)

Jira Cloud must reach the service over HTTPS. A Cloudflare quick tunnel does this for free, without an account.

Install `cloudflared` once (Ubuntu):

```bash
curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb
```

Start the tunnel (a third terminal, keep it open):

```bash
cloudflared tunnel --url http://localhost:8765
```

If it keeps logging `Failed to dial a quic connection ... timeout: no recent network activity`, the network blocks QUIC (UDP port 7844, common on university and office networks). Use HTTP/2 over port 443 instead:

```bash
cloudflared tunnel --protocol http2 --url http://localhost:8765
```

It prints an address like `https://random-words.trycloudflare.com`. Check it from anywhere: `https://random-words.trycloudflare.com/health` should show `{"ok": true}`.

**The address changes every time the tunnel restarts.** Then update the URL in the Jira rule (step 6.3). A fixed address needs a named tunnel (a Cloudflare account and a domain) or a VM.

## 6. Create the Jira rule (no code)

1. Jira → project **SPEC** → **Project settings** → **Automation** → **Create rule**.
2. **Trigger:** *Manual trigger from work item*. Optionally limit who can press it (for example project admins or a PM group).
3. **Action:** *Send web request*:
   - **Web request URL:** `https://random-words.trycloudflare.com/run`
   - **HTTP method:** `POST`
   - **Web request body:** *Custom data*: `{"key": "{{issue.key}}"}`
   - **Headers:** `Content-Type` = `application/json`, `X-SpecBridge-Secret` = your secret (mark it hidden)
   - Leave "wait for the response" **off**. The service answers at once, and the run continues in the background.
4. Name the rule **Run SpecBridge**, save it, and turn it on.

Open any SPEC ticket → **Actions** (or the ⚡ menu) → **Run SpecBridge**.

## 7. Day to day

| Task | How |
|---|---|
| See what happened | the terminal, or `data/service/service.log` (ticket keys and outcomes, no secrets); each run's full record is in `data/runs/<ticket>/` |
| See today's spending | `data/service/ledger.json` |
| Stop | Ctrl-C in the service terminal. A run in progress is stopped and queued again at the next start; waiting tickets stay queued (`data/service/queue.json`) |
| Change the limits | `config/agent.json`: `daily_budget_usd` (2.00), `queue_max` (20), `ticket_cooldown_seconds` (600), plus the per-ticket `cost_cap_usd` (0.25) |
| Finish an interrupted run without paying again | `.venv/bin/python scripts/run_ticket.py --resume --run-id <run id from the log>` |

## 8. When something goes wrong

| What you see | Likely cause | Fix |
|---|---|---|
| No comment at all after pressing the button | the tunnel or the service is down, or the rule's URL is old | check `https://<address>/health`; restart the tunnel and update the rule's URL |
| `cloudflared` repeats `Failed to dial a quic connection ... timeout` | the network blocks UDP / QUIC | start it with `--protocol http2` (section 5) |
| The rule's audit log shows **401** | the secret in the rule differs from `.env` | copy the same secret into both |
| **403** | the ticket is not in the `SPEC` project | only `SPEC` tickets can be run |
| **429** | the same ticket ran less than 10 minutes ago, the queue is full, or today's limit is reached | wait; the reason is in the response and, for the limit, on the ticket |
| The comment says "could not be generated" | Gemini or Atlassian failed during the run (for example Google "high demand") | press the button again later; details in `service.log` and the run record |
| The page shows another person's name | the token in `.env` is that person's | use the bot account (build step 8d) |

## Security

- The service listens only on this machine; the tunnel is the only way in, and every `/run` needs the secret (checked in constant time).
- Only keys of the `SPEC` project are accepted; the body is at most 4 KB of JSON; anything else is refused before a run starts.
- What a run may write is unchanged: the publish node writes only the page in the UAT space and the ticket's comment (D2, D4, D27). The service itself only writes that same `[SpecBridge]` comment ("generating", "failed", "limit reached").
- Spending is capped per ticket ($0.25) and per day ($2.00 by default, counting queued runs at their cap).

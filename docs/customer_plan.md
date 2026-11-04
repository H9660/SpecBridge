# Customer plan

Course activity 4 (AI for Product Managers capstone): five real users outside the class, how we reach them this week, and what each session should give us. Prepared 2026-10-28.

Customer evidence (notes, verbatims, scores) uses the anonymous IDs below (U1-U5), never names. This plan stays in the team's private repo.

## The five users

| ID | Name | Role | Company | Fits as | Why we want them |
|---|---|---|---|---|---|
| U1 | Vilal Ali | Software Development Engineer (SDE) | Philips | Engineer who receives UI tasks (secondary user) | Lives the problem from the build side: translating a PM's task into changes across repos and redoing work after the demo. Can judge whether our test cases are clear enough to build from. |
| U2 | Rohit Korapullu | CEO | Chessing | Product owner who hands UI tasks to engineers (primary user) | In a small company the CEO often plays the PM: writes the tasks and reviews the demo. Closest to our primary user; can judge whether the page shows the journey he meant. |
| U3 | Swati Umdekar | Engineering Manager | Walmart | Manager of engineers who build PM tasks | Sees how often work goes round again after a demo and what it costs the team. Best source for the baseline: demo-and-rework rounds per UI task. |
| U4 | Gaurav Metha | Senior Engineering Manager | Walmart | Senior manager across teams and repos | Sees the problem at scale, across several teams and multi-repo frontends. Can judge whether this would be adopted and what would block it (security, tooling, process). |
| U5 | Eric Samuel Fernando | AI Engineer | Snaphomz | Technical evaluator of AI output | Can stress-test the AI side: grounding, hallucinated screens, prompt injection, trust in a generated page. Useful for our safety and grounding criteria. |

**Gap to close:** none of the five has the job title product manager. U2 is the closest. In each session, ask for an introduction to a PM they work with, so at least two sessions are with people who write the tickets.

## How we reach them this week

| ID | Ask (by) | Proposed session | Format | Owner |
|---|---|---|---|---|
| U1 | Thu 29 Oct | Sat 31 Oct | 30-min video call | _team member_ |
| U2 | Thu 29 Oct | Sat 31 Oct | 30-min video call | _team member_ |
| U3 | Thu 29 Oct | Sun 1 Nov | 30-min video call | _team member_ |
| U4 | Fri 30 Oct | Next week (on his calendar) | 30-min video call | _team member_ |
| U5 | Thu 29 Oct | Sun 1 Nov | 30-min video call | _team member_ |

Reach each person through the channel the team member already uses with them (direct message, LinkedIn or email). Short message to send:

> Hi {name}, our team at IIIT Hyderabad is building SpecBridge, a tool that turns a Jira ticket into user-journey test cases grounded in the real code, so PM and engineers agree on the journey before anything is built. Could we take 30 minutes this week to ask how UI tasks go between PMs and engineers on your team, and get your reaction to a sample output? No preparation needed.

## What happens in a session (30 minutes)

| Time | What | What we capture |
|---|---|---|
| 0-10 min | **Their world today.** How does a UI task go from PM to engineer to demo? How often does work go round again after the demo? What does a round cost? | Baseline: demo-and-rework rounds per UI task; time per round; a real example in their words |
| 10-25 min | **Watch, don't explain.** Show a real ticket and the page SpecBridge produced for it (sample page now; the live tool once Step 8 is done). Ask them to review it as they would before building. | Where they get stuck; what they would change; which test cases they keep as they are |
| 25-30 min | **Wrap-up.** Clarity rating 1-5 ("could you build or approve from this?"). Would they use it? Who else should we talk to (a PM)? | Rating; verbatims; referrals |

**Be honest about the AI:** say it is AI-generated, show where it is unsure (its open questions), and say what happens when it can't find the code (it asks instead of guessing).

## Notes template (one per session)

| Field | Entry |
|---|---|
| ID / date / interviewer | |
| Rework rounds per UI task today (their estimate) | |
| Time lost per round | |
| Test cases kept without edits / total shown | |
| Clarity rating (1-5) | |
| Where they got stuck | |
| Verbatims (exact words, in quotes) | |
| What we will change because of this session | |
| Referrals (PMs to talk to) | |

## Status

| ID | Contacted | Session booked | Session done | Notes filed |
|---|---|---|---|---|
| U1 | | | | |
| U2 | | | | |
| U3 | | | | |
| U4 | | | | |
| U5 | | | | |

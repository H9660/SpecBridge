# Run flow: what runs when you call `run_ticket.py`

This map follows `python scripts/run_ticket.py SPEC-12 [--mode dry-run|eval|live] [--resume --run-id ID]`.
Each box is a file (and the function in it). Arrows are control paths. `[AI]` means a brain call.
Labels on arrows are the condition that picks that path.

## 1. CLI and START (before the graph runs)

```
┌──────────────────────────────────────────────┐
│ scripts/run_ticket.py  main()                │
│ parse args, set up the progress logger       │
└──────────────────────┬───────────────────────┘
                       │ run_ticket(ref, mode, run_id, resume, preflight)
                       ▼
┌──────────────────────────────────────────────┐   bad mode / bad run id /
│ specbridge/agent/graph.py  _check_request()  │── empty or too-long ref ──────────┐
└──────────────────────┬───────────────────────┘                                   │
                       ▼                                                           │
┌──────────────────────────────────────────────┐   bad value in agent.json         │
│ specbridge/agent/limits.py  load_settings()  │── (SettingsError) ────────────────┤
│   └ specbridge/env.py  load_env()  (.env)    │                                   │
│   └ config/agent.json                        │                                   │
└──────────────────────┬───────────────────────┘                                   │
                       ▼                                                           │
┌──────────────────────────────────────────────┐   data/runs not writable          │
│ graph.py  _ready_records_dir()               │── (StartError) ───────────────────┤
│ graph.py  sqlite_checkpointer()              │                                   │
│   └ data/runs/checkpoints.sqlite             │                                   │
└──────────────────────┬───────────────────────┘                                   │
                       │                                                           │
                       │  --resume and run id unknown      ─(StartError)───────────┤
                       │  new run but run id already used  ─(StartError)───────────┤
                       ▼                                                           │
┌──────────────────────────────────────────────┐   no key / bad profile /          │
│ specbridge/agent/preflight.py  check_brain() │── provider rejects (PreflightError)┤
│   └ specbridge/brain.py  load_brain()        │                                   │
│       └ config/brains.json                   │                                   │
│       └ OpenAIChatBrain (BRAIN=llm, Gemini)  │                                   │
│         or SLMHostBrain (BRAIN=slm, Kaggle)  │                                   │
└──────────────────────┬───────────────────────┘                                   │
                       │                                                           │
          mode == live and not resume?                                             │
             │ yes                     │ no                                        │
             ▼                         │                                           │
┌────────────────────────────────┐     │   Jira/Confluence unreachable             │
│ preflight.py check_atlassian() │─────┼── (PreflightError) ───────────────────────┤
│   └ specbridge/atlassian.py    │     │                                           │
└────────────┬───────────────────┘     │                                           │
             └───────────┬─────────────┘                                           │
                         ▼                                                         ▼
┌──────────────────────────────────────────────┐          ┌──────────────────────────────────┐
│ graph.py  build_graph()                      │          │ run_ticket.py prints "refused:"  │
│ wraps nodes in _main_node / _worker_node     │          │ EXIT 2  (nothing written)        │
└──────────────────────┬───────────────────────┘          └──────────────────────────────────┘
                       │
          resume and the run already finished? ── yes ──► return its old result (no work done)
                       │ no
                       ▼
               app.invoke(start | None)  ──► section 2
```

## 2. The main graph (`specbridge/agent/graph.py` wiring)

```
                         START
                           │
                           ▼
┌────────────────────────────────────────────────┐   bad URL / other site or project /
│ nodes/intake.py                                │── Jira error  (IntakeError) ──► EXIT 1
│  └ specbridge/atlassian.py  get_issue()        │   (retryable ones: "--resume")
│  └ specbridge/ticket_text.py  plain text,      │
│      redact secrets, flag AI-aimed lines       │
│  out: state.ticket                             │
└──────────────────────┬─────────────────────────┘
                       ▼
┌────────────────────────────────────────────────┐
│ nodes/understand.py                     [AI]   │
│  └ prompts/understand.md                       │
│  └ specbridge/code_index.py  CodeIndex         │
│      (registered screens near the ticket)      │
│  └ brain.ask_json  → code checks               │
│  out: state.understanding                      │
└──────────────────────┬─────────────────────────┘
                       │ route_after_understand()
          ┌────────────┴─────────────────────┐
  scope == "none"                   scope "full" / "regression"
          ▼                                  ▼
┌──────────────────────────┐   ┌────────────────────────────────────────────────┐
│ nodes/clarify.py         │   │ nodes/orchestrator.py                   [AI]   │◄──────────┐
│  questions for the PM    │   │  └ CodeIndex.search_code (hybrid)              │           │
│  └ ticket_text (redact)  │   │  └ specbridge/embedder.py (Ollama; keyword     │           │
│  status:                 │   │      fallback if down)                         │           │
│  needs-clarification     │   │  └ prompts/orchestrator.md → brain.ask_json    │           │
└────────────┬─────────────┘   │  out: work_items, brief, e2e                   │           │
             │                 └──────────────────────┬─────────────────────────┘           │
             │                                        │ route_after_orchestrator()          │
             │                 ┌──────────────────────┼─────────────────────────┐           │
             │      no work items, or       one Send per work item     2+ workers in        │
             │      status "incomplete"     (parallel)                 full scope           │
             │      (cost cap / no budget)          │                          │            │
             │                 │                    ▼                          ▼            │
             │                 │   ┌───────────────────────────┐  ┌────────────────────────┐│
             │                 │   │ worker/criterion_worker.py│  │ worker/e2e_worker.py   ││
             │                 │   │  run()  × N   (section 3) │  │  run()  × 1 (section 3)││
             │                 │   └─────────────┬─────────────┘  └───────────┬────────────┘│
             │                 │                 │  a crash → result          │             │
             │                 │                 │  status "error" (others    │             │
             │                 │                 │  are kept)                 │             │
             │                 │                 └──────────┬─────────────────┘             │
             │                 │                            ▼ (waits for all)               │
             │                 │   ┌────────────────────────────────────────────────┐       │
             │                 │   │ nodes/merge.py                  [AI, optional] │       │
             │                 │   │  code: EV-01.., TC-01.., coverage, redact      │       │
             │                 │   │  AI pass only if 2+ workers or > 8 cases:      │       │
             │                 │   │  └ prompts/merge_editor.md                     │       │
             │                 │   │  out: state.plan                               │       │
             │                 │   └──────────────────────┬─────────────────────────┘       │
             │                 │                          ▼                                 │
             │                 │   ┌────────────────────────────────────────────────┐       │
             │                 │   │ nodes/reviewer.py                       [AI]   │       │
             │                 │   │  code checks: cited files/lines exist at the   │       │
             │                 │   │  frozen commit (code_index.git), labels, neg.  │       │
             │                 │   │  cases, secrets                                │       │
             │                 │   │  AI: role "reviewer", prompts/reviewer.md,     │       │
             │                 │   │  one call per criterion                        │       │
             │                 │   │  └ limits.py  limit_reached()                  │       │
             │                 │   └──────────────────────┬─────────────────────────┘       │
             │                 │                          │ route_after_review()            │
             │                 │             ┌────────────┴─────────────────┐               │
             │                 │       final (all ok, or          weak criteria and a       │
             │                 │       round / cost limit hit)    retry allowed (round 2) ──┘
             │                 │             │
             ▼                 ▼             ▼
┌──────────────────────────────────────────────────────────────┐
│ nodes/render.py   (no AI, no network)                        │
│  one document → storage XML + HTML + Markdown + Jira comment │
│  └ data/snapshots.json (run details)                         │
└──────────────────────────────┬───────────────────────────────┘
                               │ route_after_render()
               ┌───────────────┴────────────────┐
       mode dry-run / eval                 mode live
               ▼                                ▼
┌──────────────────────────────┐  ┌─────────────────────────────────────────┐
│ nodes/save_local.py          │  │ nodes/publish.py   (only outside write) │
│  data/runs/<ticket>/<run_id>/│  │  safety checks → atlassian.py           │
│   page.html  page.md         │  │   create_page / update_page             │
│   page.storage.xml           │  │   add_comment (on the ticket)           │
│   comment.txt                │  │  a failed check → published.error       │
└──────────────┬───────────────┘  └────────────────────┬────────────────────┘
               └───────────────┬───────────────────────┘
                               ▼
                              END  ──► section 4
```

## 3. Inside one worker (`worker/criterion_worker.py`, its own small graph)

`e2e_worker.py` runs this same graph in "e2e" mode: a summary of every criterion, no starting files,
4 tool calls, `prompts/e2e.md` for writing, at most 3 flows.

```
                      START (Send payload: brief + work_item + round)
                        │
                        ▼
┌──────────────────────────────────────────────┐
│ receive_slice                                │
│  brief, own criteria, ticket lines,          │
│  starting files, limits                      │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐ ◄─────────────────────────────┐
│ agent                                  [AI]  │                               │
│  role "worker_agent", prompts/worker_agent.md│ ── no valid action ──┐        │
│  one JSON action {thought, action, args}     │    (ask again)       │        │
└──────────────────────┬───────────────────────┘ ◄────────────────────┘        │
                       │ route_after_agent()                                   │
         ┌─────────────┴─────────────────────┐                                 │
   stop (action "done", tool-call      an action to run                        │
   cap, budget or time cap)                  ▼                                 │
         │              ┌──────────────────────────────────────────────┐       │
         │              │ tools                                        │       │
         │              │  └ worker/tools.py  run() (check args)       │       │
         │              │  └ agent/code_source.py  LibrarySource,      │       │
         │              │      ToolCache (shared by all workers)       │       │
         │              │      └ specbridge/code_tools.py  CodeTools   │       │
         │              │          search_code / read_file / grep /    │       │
         │              │          find_usages                         │       │
         │              │          └ code_index.py, embedder.py        │       │
         │              │  └ worker/evidence.py  record E1, E2..;      │       │
         │              │      compact old tool output                 │       │
         │              └──────────────────────┬───────────────────────┘       │
         │                                     └───────────────────────────────┘
         ▼
┌──────────────────────────────────────────────┐
│ write_cases                            [AI]  │
│  no evidence read → no cases ("missing")     │
│  else prompts/write_cases.md (or e2e.md)     │
│  → brain.ask_json, cases cite E-ids          │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ finish  → WorkerResult only (to merge)       │
└──────────────────────────────────────────────┘
```

## 4. End of the run (back in `graph.py run_ticket()`, then the CLI)

```
                 app.invoke(...) returns or raises
                               │
   ┌───────────────┬───────────┴─────────────┬───────────────────────────┐
 Ctrl-C        IntakeError              other exception             finished normally
   │               │                         │                           │
   ▼               ▼                         ▼                           ▼
┌───────────┐  ┌──────────────┐  ┌────────────────────┐  ┌──────────────────────────────────┐
│ record    │  │ record       │  │ record "error"     │  │ status = state.status, or        │
│ "inter-   │  │ "error"      │  │                    │  │ paused (graph has a next step) / │
│ rupted"   │  │              │  │                    │  │ incomplete (a worker not done) / │
│           │  │              │  │                    │  │ complete                         │
└─────┬─────┘  └──────┬───────┘  └─────────┬──────────┘  └────────────────┬─────────────────┘
      │               │                    │                              │
      │      all go through specbridge/agent/run_record.py  write()       │
      │      → data/runs/<ticket>/<run_id>.json                           │
      ▼               ▼                    ▼                              ▼
   EXIT 130        EXIT 1               EXIT 1               run_ticket.py prints the summary
  "--resume       (retryable:          "--resume             (brain, ticket, flags, intent,
   --run-id"       --resume hint)       --run-id")            criteria, screens, risks, ...)
                                                              EXIT 0
```

## Where the AI is called

| Node | Calls per round | Brain role |
|---|---|---|
| understand | 1 | main |
| orchestrator | 1 | main |
| criterion_worker / e2e_worker | N agent turns + 1 write_cases, per worker | `worker_agent` for turns, main for writing |
| merge | 0 or 1 | main |
| reviewer | 1 per criterion | `reviewer` |

A retry round (reviewer → orchestrator) repeats orchestrator, workers, merge and reviewer for the weak criteria only.
At most 2 review rounds; the cost cap ($0.25) and time caps are checked through `limits.py`.

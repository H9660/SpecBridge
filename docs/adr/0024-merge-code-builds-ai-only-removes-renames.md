# D24 - merge: code builds the plan; the AI may only suggest removing duplicates and renaming, and code checks every suggestion

- **Status:** Accepted
- **Date:** 2026-11-11
- **Decided by:** the team (Qasim), after asking what guarantees the AI stays within its operations
- **Related:** ARCHITECTURE.md D2 (the AI gets no write access), D3 (data, not instructions), D7 (cite evidence), D17; [D23](0023-criterion-worker-design.md); `specbridge/agent/nodes/merge.py`, `prompts/merge_editor.md` (`merge_editor-v1`)

## Context

The workers run in parallel and never see each other, so their draft cases arrive with their own numbering (W1-C1, E2E-C2), their own evidence ids (every worker has an E1), repeated setup ("User is logged in" in 11 of SPEC-12's 15 cases), different names for the same screen, and possible duplicates. ARCHITECTURE.md planned a code merge plus an AI editor that removes duplicates, makes names consistent, moves shared setup into common preconditions and turns workers' notes into preconditions or end-to-end cases. The question was how to make sure an AI editor cannot drop coverage, invent claims or change what a case cites.

## Decision

1. **Code builds the plan** (no AI): the newest result per worker (retry rounds replace earlier ones); one evidence list EV-01.. where the same file and lines, or a range inside a bigger range of the same file, become one entry and every citation is rewritten; cases ordered by criterion, then happy / negative / edge / permission / empty-state, end-to-end flows last, numbered TC-01..; each keeps its `source` (the worker's id); a coverage status per criterion (covered, untestable, uncovered, skipped, failed, regression); preconditions in at least half of the cases (2+) written once as common preconditions; questions and notes de-duplicated, redacted, and injection-like ones dropped.
2. **One AI editing pass only when it is useful:** 2+ working workers or more than 8 cases. It may only suggest:
   - `remove` a case as a duplicate of another, with a reason;
   - `rename` a screen / button name to one used everywhere.
   There is no `rewrite`, no adding, merging or re-ordering, and the answer's schema has no field for citations, criteria or new cases. Workers' notes stay notes (they are not turned into cases).
3. **Every suggestion is checked by code before it is applied** (and every applied or refused suggestion is listed in `plan["changes"]` with the reason):
   - a removal needs both cases to exist, the same criteria, the same type, and at least 60% the same words in steps + expected result (so "edit the title" and "edit the title on tablet" are kept apart), and it never takes a criterion's last case;
   - a rename must go to a name that appears in the code excerpts, the brief's screens / registered names or the ticket, and the old name must appear in some case.
4. **Whole-plan checks, all or nothing:** after the edits every criterion that was covered is still covered, every case cites existing evidence, no case id is new and no case's criteria changed. If any check fails, all the AI's edits are dropped and the code-built plan is used. If the call fails, the code-built plan is used.
5. The AI never writes anything: it returns one JSON answer; code applies it (D2).

## Consequences

- The plan can never come out of merge worse-formed than code alone makes it; the AI can only shorten it (true duplicates) and make names consistent.
- Measured on SPEC-12's real 15 cases (`data/live_checks/2026-11-11-merge.md`): 8 citations became 4 evidence entries, 2 common preconditions moved to the top, all 6 criteria covered; the AI suggested no change (the near-duplicates test different screen sizes); $0.008, 58 s.
- Wording stays as the workers wrote it; unclear wording is for the reviewer (node 8) to flag and can be revisited in Step 10 (a checked `rewrite` operation could be added then).
- Cost: $0 for 1-worker tickets with few cases; about $0.008-0.012 otherwise.

## Alternatives considered

- **A `rewrite` operation** (clearer titles, steps, expected results): useful, but it could subtly change what a case checks (for example dropping a number); left out for now.
- **Letting the AI turn notes into cases** (as first planned): those would be claims no worker checked against code.
- **Code only:** no duplicate detection by meaning and no name clean-up.
- **The AI finds common preconditions:** code does it deterministically by counting.

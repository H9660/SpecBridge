# Live check: orchestrator (node 4) on real tickets - 2026-11-10

Command: `BRAIN_MODEL=gemini-3.6-flash .venv/bin/python scripts/run_ticket.py <ticket> --no-preflight` (dry-run).
Model `gemini-3.6-flash` because `gemini-3.8-flash` was overloaded (HTTP 503); costs are estimates at 3.8-flash list prices.
Graph: START -> intake -> understand -> orchestrator -> END (workers, node 5, not built yet). Prompts: `understand-v3`, `orchestrator-v1` (ADR D22).

| Ticket | Criteria | Plan | Expected | OK |
|---|---|---|---|---|
| SPEC-66 | 3 (one sorting behaviour on two screens) | 1 worker, no e2e | one worker for the sorting rules | yes |
| SPEC-14 | 9 | 2 workers + e2e; AC9 ("add tests") set aside as not testable in a browser | fewer than 5 workers, not several in the same files (the code-only prototype gave 5) | yes |

Full run records: `data/runs/SPEC-66/20261110-000618-791b2c.json`, `data/runs/SPEC-14/20261110-000807-73ba6d.json` (git-ignored).

## SPEC-66

```
ticket: SPEC-66  Story  "Allergies widget: list the most severe allergies first"  status: To Do
intent: Display patient allergies ordered by severity first (severe, moderate, mild) and then by date with the most recent first, consistently across the patient summary and full allergies page.
criteria: 3 (3 stated, 0 inferred, 0 conflicting/unclear)
  AC1 [stated] Allergies are ordered by severity, showing severe first, followed by moderate, then mild.
  AC2 [stated] Allergies with the same severity level are ordered with the most recent first.
  AC3 [stated] The allergy list ordering is identical on both the patient summary widget and the full Allergies page.
screens: patient summary (changed, in code), full Allergies page (changed, in code)
risks:  injection-attempt   domain: fits
  ? How should allergies with unknown or unrecorded severity be ordered in the list?
testable: yes - checkable criteria found
AI:     gemini-3.6-flash, 4072 tokens, ~$0.0082, 10.36 s
plan:   1 worker(s); search hybrid; grouping by AI refinement
  W1 AC1, AC2, AC3: Verify that patient allergies are consistently ordered by severity and then recency on both the patient summary widget and the full Allergies page.
     starts at: utils.ts; allergies-tile.extension.tsx; index.ts; allergy-intolerance.resource.ts
budget: $0.2377 left of $0.25; $0.1902 per worker, reserve $0.0476, 12 tool calls each
run:    20261110-000618-791b2c
status: complete (stopped after the orchestrator: the workers (node 5) are not built yet)
```

The first attempt failed with HTTP 503 (high demand); this is the resumed run.

## SPEC-14

```
ticket: SPEC-14  Story  "Support concept reference ranges in the Angular form engine"  status: To Do
intent: The Angular form engine should validate numeric observation questions using patient-specific concept reference ranges fetched from the backend, while keeping any stricter bounds defined in the form schema.
criteria: 9 (9 stated, 0 inferred, 0 conflicting/unclear)
  AC1 [stated] Fetch the patient-applicable reference range for each numeric observation question.
  AC2 [stated] Support concepts defined by UUID or concept mapping.
  AC3 [stated] Use the lowAbsolute and hiAbsolute values for validation.
  AC4 [stated] Apply the range before the form is created.
  AC5 [stated] Keep any stricter min or max already defined in the form schema.
  AC6 [stated] Apply a range when both effective bounds can be determined.
  AC7 [stated] Support nested numeric questions.
  AC8 [stated] Continue loading the form when offline or when the backend does not support the resource.
  AC9 [stated] Add tests showing that the range returned by the backend is applied, including a lower bound of zero.
screens: form (changed, in code)
risks:  none   domain: fits
testable: yes - checkable criteria found
AI:     gemini-3.6-flash, 4421 tokens, ~$0.0096, 12.17 s
plan:   2 worker(s) + e2e worker; search hybrid; grouping by AI refinement
  W1 AC1, AC2, AC3, AC4, AC5, AC6, AC7: Verify that numeric observation fields, including nested fields and concepts configured by UUID or mapping, correctly apply patient reference range limits and preserve stricter form schema bounds duri
     starts at: interpretation-utils.ts; numeric-observation.component.tsx; use-concept-reference-range.ts; numeric-observation.stories.tsx
  W2 AC8: Verify that forms load and remain functional when working offline or when the backend reference range service is unavailable.
     starts at: offline-form-helpers.ts; offline-forms-overview-card.component.tsx; index.ts; offline-forms.component.tsx
  skipped AC9: not testable in a browser: Adding automated codebase tests is a software development task verified via test suites, not via browser manual testing.
budget: $0.2317 left of $0.25; $0.0741 per worker, reserve $0.0463, 12 tool calls each
run:    20261110-000807-73ba6d
status: complete (stopped after the orchestrator: the workers (node 5) are not built yet)
```

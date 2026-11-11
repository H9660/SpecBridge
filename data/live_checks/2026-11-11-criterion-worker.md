# Live check: criterion_worker (node 5) on real tickets - 2026-11-11

Command: `.venv/bin/python scripts/run_ticket.py <ticket> --no-preflight` (dry-run). Models: search turns `gemini-3.5-flash-lite` (brains.json role `worker_agent`), everything else `gemini-3.8-flash`. Limits: 8 tool calls per worker, $0.25 per ticket. Prompts: `understand-v3`, `orchestrator-v1`, `worker_agent-v1`, `write_cases-v1` (ADR D23). Costs are estimates at list price.
Graph: START -> intake -> understand -> orchestrator -> Send -> criterion_worker x N -> END (merge, node 7, not built yet).

| Ticket | Workers | Test cases | Untestable | Cost | Wall time | Verdict |
|---|---|---|---|---|---|---|
| SPEC-66 (allergies sorted by severity) | 1 | 6 (AC1-AC3: happy, edge, empty-state), every case cites code read | 0 | $0.057 | 119 s | as expected; cases cite `severityOrder` in `utils.ts` and the allergies list extension |
| SPEC-14 (reference ranges in the Angular form engine) | 3 in parallel | 2 (AC8 offline / unsupported backend) | 8 | $0.100 | 132 s | the Angular form engine is not in the 5 frozen repos; the workers said so instead of inventing screens |

Findings:
1. The workers do not invent UI: with no code for a criterion they mark it untestable with the reason (SPEC-14).
2. A worker whose criteria are all untestable still ends `complete` (every criterion handled); the ticket page and the reviewer need to make that visible.
3. The orchestrator's AI split differs by model: SPEC-14 gave 2 workers on `gemini-3.6-flash` (2026-11-10) and 3 on `gemini-3.8-flash`; AC9 ("add tests") was set aside by 3.6 but not by 3.8.
4. W2 on SPEC-14 started from unrelated files (billing form, visit date) because the search found nothing about form-schema bounds; it used its 8 tool calls without finding the code.

Full run records: `data/runs/SPEC-66/20261111-150433-e75489.json`, `data/runs/SPEC-14/20261111-150648-737a44.json` (git-ignored).

## SPEC-66

```
ticket: SPEC-66  Story  "Allergies widget: list the most severe allergies first"  status: To Do
intent: Display patient allergies sorted by severity and recency across the patient summary and the full Allergies page.
criteria: 3 (3 stated, 0 inferred, 0 conflicting/unclear)
  AC1 [stated] Allergies are listed by severity: severe first, then moderate, then mild.
  AC2 [stated] Allergies that have the same severity are listed with the most recent first.
  AC3 [stated] The sort order is identical on the patient summary and on the full Allergies page.
screens: Allergies widget (changed, in code), patient chart (used, in code), patient summary (changed, in code), full Allergies page (changed, in code)
risks:  injection-attempt   domain: fits
  ? Where should allergies with an unknown or unspecified severity be placed in the sorted list?
testable: yes - Clear UI acceptance criteria exist for listing and ordering allergies across the patient summary and allergy details views.
AI:     gemini-3.8-flash, 4891 tokens, ~$0.0113, 34.58 s
plan:   1 worker(s); search hybrid; grouping by AI refinement
  W1 AC1, AC2, AC3: Verify that allergies are sorted by severity and recency consistently on both the patient summary and the full Allergies page.
     starts at: utils.ts; allergies-tile.extension.tsx; index.ts; allergy-intolerance.resource.ts
budget: $0.2362 left of $0.25; $0.1889 per worker, reserve $0.0472, 8 tool calls each
worker W1 (AC1, AC2, AC3): complete; 7 tool calls, 20 pieces of code read, stop: done
  W1-C1 [AC1, happy] Verify allergies are sorted by severity with severe first, moderate second, and mild last on patient summary  (cites E1, E3)
  W1-C2 [AC1, edge] Display allergy tag with unknown severity alongside severe and mild allergies  (cites E1, E3)
  W1-C3 [AC2, happy] Verify allergies with the same severity are ordered with the most recent first  (cites E1, E3, E5)
  W1-C4 [AC2, edge] Verify allergies with the same severity and identical update timestamps both render cleanly  (cites E1, E3, E5)
  W1-C5 [AC3, happy] Verify allergy sort order on the full Allergies page matches the patient summary  (cites E1, E3, E4, E5)
  W1-C6 [AC3, empty-state] Verify consistent empty state display when patient has no allergies recorded  (cites E3, E4)
run:    20261111-150433-e75489
status: complete (stopped after the workers: merge (node 7) is not built yet)
```

## SPEC-14

```
ticket: SPEC-14  Story  "Support concept reference ranges in the Angular form engine"  status: To Do
intent: Validate numeric questions in Angular forms using patient-specific concept reference ranges alongside form schema bounds.
criteria: 9 (9 stated, 0 inferred, 0 conflicting/unclear)
  AC1 [stated] Fetch patient-applicable reference ranges for each numeric observation question.
  AC2 [stated] Support concepts defined by UUID or concept mapping.
  AC3 [stated] Use the lowAbsolute and hiAbsolute values from the reference range for numeric validation.
  AC4 [stated] Apply the concept reference range before the form is rendered.
  AC5 [stated] Retain any stricter min or max values already configured in the form schema.
  AC6 [stated] Apply a range validation only when both effective bounds can be determined.
  AC7 [stated] Support reference range validation for nested numeric questions.
  AC8 [stated] Continue loading the form normally when offline or when the backend does not support the concept reference range resource.
  AC9 [stated] Apply the backend-returned range including cases where the lower bound is zero.
screens: form (changed, in code)
risks:  none   domain: fits
  ? What validation message or visual error indicator should be displayed when a user inputs a numeric value outside the concept reference range?
testable: yes - checkable criteria found
AI:     gemini-3.8-flash, 4606 tokens, ~$0.0102, 19.51 s
plan:   3 worker(s) + e2e worker; search hybrid; grouping by AI refinement
  W1 AC1, AC2, AC3, AC7, AC9: Test numeric question validation in forms against patient reference ranges, including concepts defined by UUID or mapping, nested questions, and zero lower bounds.
     starts at: reference-range-helpers.ts (shared); helpers.ts (shared); interpretation-utils.ts; numeric-observation.stories.tsx
  W2 AC5, AC6: Test boundary rules when resolving form schema limits with reference ranges and requiring both effective bounds.
     starts at: vitals-biometrics-input.component.tsx; billable-service-form.workspace.tsx; visit-date-time.component.tsx; validators.ts
  W3 AC4, AC8: Test form loading behavior when applying reference ranges before render and falling back gracefully when offline or unsupported.
     starts at: helpers.ts (shared); data.resource.ts (shared); use-concept-reference-range.ts (shared); vitals-biometrics-form.utils.ts
budget: $0.2215 left of $0.25; $0.0506 per worker, reserve $0.0443, 8 tool calls each
worker W1 (AC1, AC2, AC3, AC7, AC9): complete; 8 tool calls, 30 pieces of code read, stop: tool-call limit reached
  untestable AC1: The evidence does not contain Angular form engine code, form UI components, or on-screen labels to verify fetching or applying patient-applicable reference ranges in the browser.
  untestable AC2: The evidence contains only React styleguide utilities and no Angular form engine schema handling or form UI to test concept mapping versus UUID resolution in the browser.
  untestable AC3: No form controls, input labels, or validation error messages are present in the evidence to test lowAbsolute and hiAbsolute validation in the browser without inventing UI elements.
  untestable AC7: No Angular form engine templates, nested question/obs group structures, or UI labels exist in the evidence to test nested numeric question reference ranges.
  untestable AC9: No browser UI elements, form inputs, or validation feedback indicators are available in the evidence to verify lower bound zero range enforcement.
worker W2 (AC5, AC6): complete; 8 tool calls, 15 pieces of code read, stop: tool-call limit reached
  untestable AC5: The provided evidence (E1–E15) contains login E2E specs and implementer tools files, but no code from the Angular form engine. Without the form engine source code defining numeric question inputs, form schema min/max handling, or validation UI, UAT browser steps and expected outcomes cannot be specified without inventing UI elements.
  untestable AC6: The provided evidence (E1–E15) does not include any Angular form engine code or UI implementations showing how numeric questions are rendered, how effective bounds are evaluated, or how range validation is visually indicated when one or both bounds are absent.
worker W3 (AC4, AC8): complete; 2 tool calls, 2 pieces of code read, stop: done
  W3-C1 [AC8, happy] Form loads normally when backend does not support concept reference range resource  (cites E1, E2)
  W3-C2 [AC8, edge] Form loads normally when browser is offline  (cites E1, E2)
  untestable AC4: Applying the concept reference range before the form is rendered describes an internal lifecycle timing mechanism during form engine initialization. The provided evidence only includes a React hook (useConceptReferenceRange in esm-styleguide) rather than the Angular form engine implementation, and there are no observable UI indicators or elements provided to verify pre-render application in the browser.
run:    20261111-150648-737a44
status: complete (stopped after the workers: merge (node 7) is not built yet)
```

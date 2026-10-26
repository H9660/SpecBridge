# Step 1 smoke test - 2026-10-26 23:37

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Config lists 4-5 repos | PASS | core, patient-chart, patient-management, billing-app, dispensing-app |
| 2 | Every repo reachable on GitHub | PASS | 5/5 |
| 3 | Each repo pinned to a real commit on main, dated before cutoff | PASS | all 5 before 2026-04-01 |
| 4 | No duplicate tickets in shortlist | PASS | 63 tickets |
| 5 | Shortlist has enough tickets for a 30-50 golden set | PASS | 63 |
| 6 | Every ticket exists in public Jira | PASS | 63/63 |
| 7 | Every ticket is finished (Done) | PASS | all Done |
| 8 | Every ticket has a description | PASS | all have text |
| 9 | No ticket's fix is already inside the frozen code | PASS | 0 leaks |
| 10 | Changed files exist in frozen code (something real to find) | WARN | avg 86% of changed files already existed; 2 tickets only add new files |
| 11 | Readable shortlist matches the data | PASS | 63 rows vs 63 picked |

## Warnings

- Tickets whose changes are all new files (SpecBridge can only point to the nearby screen, not an existing file): O3-5742, O3-5729

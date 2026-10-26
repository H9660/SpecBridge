# Step 2 smoke test - 2026-10-26 23:36

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Download folder exists and is outside OneDrive | PASS | C:\specbridge-work |
| 2 | All repos on their frozen version, complete, unchanged | PASS | 5/5 OK |
| 3 | Files the golden tickets touched are readable on disk | PASS | 256/256 files |
| 4 | No downloaded repos inside the (OneDrive) project folder | PASS | 1.2 MB of project files; nested repos: none |
| 5 | Secrets file (.env) is git-ignored | PASS | .gitignore |
| 6 | .env is not tracked by git | PASS |  |
| 7 | .env.example lists every setting | PASS | ATLASSIAN_SITE, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN, JIRA_PROJECT_KEY, CONFLUENCE_SPACE_KEY |
| 8 | Copier removes PR refs, links back, mentions, attachments (built-in example) | PASS | {'pr_links': 2, 'source_links': 1, 'attachments': 1, 'mentions': 1} |
| 9 | All 63 tickets prepared with valid descriptions | PASS | 63 prepared; invalid: none |
| 10 | No answer-revealing links left in any copied ticket | PASS | 0 left |
| 11 | Ticket titles are unique (needed so re-runs don't duplicate) | PASS | 63 unique of 63 |
| 12 | Tickets that name code files (flagged, kept as written) | WARN | 18: O3-5714, O3-5836, O3-5823, O3-5981, O3-5918, O3-6098, O3-5917, O3-5919, O3-5914, O3-5916, O3-5680, O3-6112, O3-5816, O3-5874, O3-5588, O3-5650, O3-5632, O3-5645 |
| 13 | Can log in to the team's Atlassian site | PASS | Hussain Lohawala |
| 14 | Jira project exists with Story/Task types | PASS | SPEC: ['Bug', 'Epic', 'Story', 'Subtask', 'Task'] |
| 15 | Confluence space exists | PASS | UAT: SpecBridge UAT |
| 16 | All 63 tickets copied into team Jira | PASS | 63/63 (run scripts/import_tickets.py) |

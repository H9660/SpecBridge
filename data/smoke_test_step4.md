# Step 4 smoke test - 2026-10-27 02:36

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | 4a Index was built from the frozen version of all 5 repos | PASS | 5 repos; not frozen: none |
| 2 | 4a Every code file (.ts/.tsx/.js/.jsx) is in the index | PASS | 2322 indexed, 2322 in the repos (1755 non-test) |
| 3 | 4a Index file lives with the repos, outside the git project | PASS | /home/qasim/Documents/sem3/AutoSE/Project/specbridge-work/specbridge_index.sqlite |
| 4 | 4a Re-running the build skips work when the code has not changed | PASS | up to date, not rebuilt |
| 5 | 4a Code names are split into words, ticket filler words dropped | PASS | 'paginated vitals'; ['vitals', 'notes'] |
| 6 | 4a Hand query finds the vitals widget code in the top 10 | PASS | packages/esm-patient-vitals-app/src/vitals-biometrics-form/exported-vitals-biometrics-form.workspace.tsx |
| 7 | 4a Repo filter and test-file filter work | PASS | 10 hits in patient-management only; tests appear only when asked |
| 8 | 4a Empty or filler-only text returns nothing instead of failing | PASS | [] |
| 9 | 4b Files are split into pieces of at most ~1,500 tokens | PASS | 3827 pieces; largest 5999 chars; 2 files with only imports have none |
| 10 | 4b Pieces carry name, kind, line range and on-screen text | PASS | ('StartVisitButton (+2)', 'component', 6, 47); text: ['Error starting visit', 'An error occurred while starting the visit', 'Start visit'] |
| 11 | 4b Files know where they appear in the app (routes.json), passed down to what they import | PASS | 605 files labelled (323 through imports); vitals summary: widget vitals-overview-widget in patient-chart-summary-dashboard-slot |
| 12 | 4d Links: imports, names from @openmrs packages resolved into core, UI wiring | PASS | {'import': 2644, 'package': 3074, 'ui': 410} |
| 13 | 4d UI wiring links repos: start-visit button (patient-chart) <-> patient search banner (patient-management) | PASS | via start-visit-button-slot |
| 14 | 4d Tool search_code: files with best piece, lines and where they appear | PASS | 5 results; start-visit button at #2 |
| 15 | 4d Tool read_file reads line ranges and only files in the library | PASS | 47 lines in file; outside path -> core/../../../etc/passwd is not a code file in the library |
| 16 | 4d Tool grep finds exact text across repos; bad patterns give an error | PASS | 5 matches |
| 17 | 4d Tool find_usages lists links in both directions, across repos | PASS | 4 links |
| 18 | 4c Every piece embedded once; re-running skips done pieces; document/query prefixes sent | PASS | 3827 pieces, then 0; prefixes ['search_document', 'search_query'] |
| 19 | 4c Search by meaning and hybrid search run end to end (fake vectors) | PASS | top piece PatientSearchTabPanel (+1); start-visit button in hybrid top 10: True |
| 20 | 4c Live embedder (nomic-embed-text) works and puts similar meanings closer | PENDING | cannot reach ollama at http://127.0.0.1:11434 (is `ollama serve` running?): <urlopen error [Errno 111] Connection refused> |
| 21 | 4a Golden tickets scored (2 skipped: their changed files did not exist yet) | PASS | 63 tickets, 61 scored, skipped ['O3-5742', 'O3-5729'] |
| 22 | 4d Final search (combined) is at least as good as the keyword baseline | PASS | hit@10 0.79 -> 0.80; recall@20 0.63 -> 0.66; cross-repo recall@20 -> 0.52 |
| 23 | Step 4 search reaches the provisional bar (hit@10 >= 0.8 on tickets without file names) | WARN | combined: hit@10 0.80 all / 0.74 without file names; mrr 0.53 (data/retrieval/combined.md) |
| 24 | 4c Hybrid search (keywords + meaning + links) scored | PENDING | needs Ollama working; then run scripts/eval_retrieval.py --method hybrid with .venv/bin/python |
| 25 | Search is fast | PASS | 19.8 ms per ticket |

# Repo stats: OpenMRS 3 snapshots vs handoff §3.1

Generated 2026-10-27 by `uv run python scripts/repo_stats.py --snapshots`. Re-run to refresh.

Read the NO rows with these notes:

- **Issue tracker:** GitHub issues are disabled on all five repos. OpenMRS tracks issues in its own Jira (project **O3**), which is where the golden tickets come from. Met in practice, through an external tracker.
- **Licence:** MPL-2.0 plus the OpenMRS healthcare disclaimer. This is weak (file-level) copyleft, **not permissive**, so the criterion is not met as written. **Team decision needed:** is MPL acceptable? SpecBridge only reads the code, but run traces and outputs under `runs/` will be committed and will contain MPL-licensed code snippets.

## https://github.com/openmrs/openmrs-esm-core.git
- Commit: `cf088d5277b12b39022095ce4a9ec9e70e8373e3`
- Code files: 544 non-test (686 incl. tests) {'.js': 16, '.ts': 346, '.tsx': 182}
- Lines (non-blank, non-test): 34,653
- Routers: {"react-router": {"files_importing": 13, "routes": 13}, "single-spa routes.json": {"apps": 6, "pages": 10, "extensions": 29, "workspaces": 0, "modals": 4}}
- Licence: MPL-2.0 + disclaimer (GitHub: NOASSERTION) ['LICENSE']

| Criterion | Meets | Detail |
|---|---|---|
| React + TypeScript | yes | 528 .ts/.tsx files |
| Multiple routes/screens | yes | react-router, single-spa routes.json |
| Active issue tracker | NO | 0 open GitHub issues (GitHub issues DISABLED - the project tracks issues elsewhere; check it by hand) |
| Under 3000 TS/TSX files | yes | 544 non-test code files |
| Permissive licence | NO | weak copyleft: MPL-2.0 + disclaimer (GitHub: NOASSERTION) |

## https://github.com/openmrs/openmrs-esm-patient-chart.git
- Commit: `8ede2e3a641d470abcd31fe496f5714f2b4fc600`
- Code files: 537 non-test (757 incl. tests) {'.js': 45, '.ts': 241, '.tsx': 251}
- Lines (non-blank, non-test): 46,223
- Routers: {"react-router": {"files_importing": 6, "routes": 4}, "single-spa routes.json": {"apps": 19, "pages": 1, "extensions": 81, "workspaces": 0, "modals": 18}}
- Licence: MPL-2.0 + disclaimer (GitHub: NOASSERTION) ['LICENSE']

| Criterion | Meets | Detail |
|---|---|---|
| React + TypeScript | yes | 492 .ts/.tsx files |
| Multiple routes/screens | yes | react-router, single-spa routes.json |
| Active issue tracker | NO | 0 open GitHub issues (GitHub issues DISABLED - the project tracks issues elsewhere; check it by hand) |
| Under 3000 TS/TSX files | yes | 537 non-test code files |
| Permissive licence | NO | weak copyleft: MPL-2.0 + disclaimer (GitHub: NOASSERTION) |

## https://github.com/openmrs/openmrs-esm-patient-management.git
- Commit: `37d3c1bce6ce05907625761c593077e4eae4613e`
- Code files: 494 non-test (675 incl. tests) {'.js': 21, '.ts': 144, '.tsx': 329}
- Lines (non-blank, non-test): 36,387
- Routers: {"react-router": {"files_importing": 31, "routes": 27}, "single-spa routes.json": {"apps": 9, "pages": 5, "extensions": 61, "workspaces": 1, "modals": 27}}
- Licence: MPL-2.0 + disclaimer (GitHub: NOASSERTION) ['LICENSE.md']

| Criterion | Meets | Detail |
|---|---|---|
| React + TypeScript | yes | 473 .ts/.tsx files |
| Multiple routes/screens | yes | react-router, single-spa routes.json |
| Active issue tracker | NO | 0 open GitHub issues (GitHub issues DISABLED - the project tracks issues elsewhere; check it by hand) |
| Under 3000 TS/TSX files | yes | 494 non-test code files |
| Permissive licence | NO | weak copyleft: MPL-2.0 + disclaimer (GitHub: NOASSERTION) |

## https://github.com/openmrs/openmrs-esm-billing-app.git
- Commit: `6a0f80980e71807345ae412fb587bb9d57012bda`
- Code files: 64 non-test (112 incl. tests) {'.js': 4, '.ts': 15, '.tsx': 45}
- Lines (non-blank, non-test): 5,666
- Routers: {"react-router": {"files_importing": 6, "routes": 6}, "single-spa routes.json": {"apps": 1, "pages": 1, "extensions": 10, "workspaces": 0, "modals": 7}}
- Licence: MPL-2.0 + disclaimer (GitHub: NOASSERTION) ['LICENSE']

| Criterion | Meets | Detail |
|---|---|---|
| React + TypeScript | yes | 60 .ts/.tsx files |
| Multiple routes/screens | yes | react-router, single-spa routes.json |
| Active issue tracker | NO | 0 open GitHub issues (GitHub issues DISABLED - the project tracks issues elsewhere; check it by hand) |
| Under 3000 TS/TSX files | yes | 64 non-test code files |
| Permissive licence | NO | weak copyleft: MPL-2.0 + disclaimer (GitHub: NOASSERTION) |

## https://github.com/openmrs/openmrs-esm-dispensing-app.git
- Commit: `7f604ab79d7c5120fde2ea1ebdb11241cbd0478c`
- Code files: 58 non-test (92 incl. tests) {'.js': 4, '.ts': 10, '.tsx': 44}
- Lines (non-blank, non-test): 6,115
- Routers: {"react-router": {"files_importing": 1, "routes": 0}, "single-spa routes.json": {"apps": 1, "pages": 1, "extensions": 8, "workspaces": 0, "modals": 4}}
- Licence: MPL-2.0 + disclaimer (GitHub: NOASSERTION) ['LICENSE']

| Criterion | Meets | Detail |
|---|---|---|
| React + TypeScript | yes | 54 .ts/.tsx files |
| Multiple routes/screens | yes | react-router, single-spa routes.json |
| Active issue tracker | NO | 0 open GitHub issues (GitHub issues DISABLED - the project tracks issues elsewhere; check it by hand) |
| Under 3000 TS/TSX files | yes | 58 non-test code files |
| Permissive licence | NO | weak copyleft: MPL-2.0 + disclaimer (GitHub: NOASSERTION) |

**Combined:** 1697 non-test code files, 129,044 lines (under the 3000-file guide)

# Where the build differs from SPECBRIDGE_HANDOFF.md

The handoff was written as if the project were starting from nothing. Steps 1-4 (see [BUILD_STEPS.md](BUILD_STEPS.md)) were already built when it arrived. On 2026-10-27 the user chose to **merge**: keep what exists and fit the handoff's structure around it. Each difference is listed here so a reviewer can see that it was a choice, not a slip.

| # | Handoff says | What we do | Why | Status |
|---|---|---|---|---|
| 1 | One React/TS repo; "no multi-repo" (§2.2, §15) | 5 OpenMRS 3 repos at pinned commits | User decision 2026-10-26, confirmed 2026-10-27. The 63 golden candidates (incl. cross-repo tickets) depend on it | Decided |
| 2 | Twenty or Plane | OpenMRS 3 | As above. Stats against §3.1: [repo_stats_openmrs.md](repo_stats_openmrs.md) | Decided |
| 3 | ChromaDB vector store (§4) | SQLite + FTS5 + numpy (`specbridge/code_index.py`) | User decision 2026-10-27: keyword + vector + link joins in one file, no server | Decided |
| 4 | tree-sitter chunking (§4, §7) | Existing parser `specbridge/code_parse.py` | "No extra packages unless scores show a need, and asked first" (2026-10-27) | Revisit in Phase 1 if chunk quality is the bottleneck |
| 5 | Route adapters for react-router and Next.js (§7.6) | OpenMRS screens come from single-spa `routes.json` (pages, extensions/slots, workspaces, modals) plus some react-router inside apps | That is how OpenMRS wires screens. `repo_stats` finds both | Phase 1 needs a `routes.json` adapter |
| 6 | `CodeChunk.chunk_id = "<path>:<start>-<end>"` (§6.2) | **Not changed yet** (models.py copies §6 exactly) | Paths collide across 5 repos (e.g. `src/index.ts`). Needs `<repo>/<path>:<start>-<end>` | Needs team OK before Phase 1 |
| 7 | `CodeChunk.kind` = component/hook/function/class/module/route_config | **Not changed yet** | The existing parser also produces workspace, modal, resource (SWR hooks) and extension pieces | Map onto existing kinds, or extend the Literal (team decides) |
| 8 | Live Jira/Confluence only in Phase 7 | Jira project `SPEC` (63 tickets) and Confluence space `UAT` already exist | Built in Steps 1-2 as golden-ticket storage. The agent does not read from or write to them before Phase 7 | Kept, unused by the pipeline |
| 9 | `CLAUDE.md` exactly as §15 | Copied verbatim, so it still says "one React/TS repo… no multi-repo" | The user asked for the exact text | Change the scope line once the team approves #1 |
| 10 | Model calls through `llm.py` (LiteLLM) | `llm.py` added. The older `brain.py` (Step 3) stays for its smoke test | Both honour `BRAIN=llm|slm` and `BRAIN_MODEL`, which the SLM course needs | Move callers to `llm.py` from Phase 2 on |
| 11 | Golden pairs in `golden/drafts/`, versions in `golden/vN/` | The Step 1 candidates stay in `data/golden/` (picked tickets plus changed-file ground truth). No `GoldenPair` files exist yet | Handoff: no golden pairs before the repo is confirmed | Team writes pairs after Phase 1 is approved |
| 12 | Repo stats include open issue count via `gh` | GitHub issues are disabled on all OpenMRS repos | OpenMRS uses its own Jira (project O3), which is our ticket source | Met in practice |
| 13 | Permissive licence (§3.1) | OpenMRS is MPL-2.0 plus a healthcare disclaimer: weak copyleft, not permissive. `repo_stats` reports NO | Criterion not met as written. Read-only use, but committed run traces will contain MPL code snippets | **Team decision needed** |

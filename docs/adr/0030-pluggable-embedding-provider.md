# D30 - Embeddings: local nomic-embed-text through Ollama, behind a small provider interface so other models can be added

- **Status:** Proposed
- **Date:** 2026-11-26
- **Decided by:** Part 1 (Ollama and `nomic-embed-text`) was decided by the user on 2026-10-26 and 2026-10-27, before ADRs existed. Parts 2-4 (the interface, the vector key, the switch rules) are proposed by Claude and wait for the user's approval.
- **Related:** ARCHITECTURE.md D5 (one code-reading interface); [D22](0022-orchestrator-code-proposes-ai-refines.md) (orchestrator search); [D29](0029-slm-brain-on-kaggle-host.md) (the brain is swappable; embeddings are not part of the brain); USER_CLARIFICATIONS.md 2026-10-26, 2026-10-27 (three rows); BUILD_STEPS.md Step 4c; `specbridge/embedder.py`, `config/embedder.json`, `specbridge/code_index.py` (`piece_vectors`, `build_vectors`, `search_vectors`), `specbridge/agent/code_source.py`, `specbridge/agent/nodes/orchestrator.py`

## Context

Search by meaning was added in Step 4c. It runs beside keyword search, and the two lists are merged. It helps most on vague tickets:

| Tickets | hit@10 without / with meaning | recall@20 without / with meaning |
|---|---|---|
| all (61) | 0.80 / 0.84 | 0.66 / 0.73 |
| no file names in ticket (43) | 0.74 / 0.79 | 0.60 / 0.70 |
| vague (17) | 0.59 / 0.71 | 0.59 / 0.73 |

What was decided then, and where it is written down:

| Date | Decision | Where |
|---|---|---|
| 2026-10-26 | Embeddings run locally, not in the cloud | USER_CLARIFICATIONS.md |
| 2026-10-27 | `nomic-embed-text` through Ollama, chosen over MiniLM and Gemini Embedding 2. Gemini can be compared later if search falls short. | USER_CLARIFICATIONS.md |
| 2026-10-27 | The model reads up to 2,048 tokens, so pieces are capped at 6,000 characters (about 1,500 tokens). A code-specific model can be compared in Step 10. | USER_CLARIFICATIONS.md |

These decisions were never recorded as a design decision. The code also has gaps that would surprise a reader who wants to try another model:

- **Only one provider.** `config/embedder.json` has a `provider` field, but `load_embedder()` accepts only `"ollama"`.
- **Nomic rules are mixed in with general settings.** The `search_document: ` / `search_query: ` prefixes are nomic's convention. Other models need different prefixes or none at all.
- **Vectors are keyed by model name only.** `piece_vectors` stores `(piece_id, model, vector)`. If two providers use the same model name, their vectors mix. Vectors of a different length would then break the numpy search.
- **Switching is silent.** If `EMBED_MODEL` names a model with no vectors, `vector_count()` is 0. Search then quietly drops to keywords plus links, and the run record does not say so.

## Decision

1. **Keep the current setup as the default.** Local `nomic-embed-text` through Ollama at `127.0.0.1:11434`. The settings stay in `config/embedder.json`, and `EMBED_MODEL` can override the model. Nothing changes for current runs.

2. **One small interface for every provider.** An embedder is any object with:

   | Member | Meaning |
   |---|---|
   | `model_key` | A string that names the vectors in the database: `"<provider>:<model>"`, e.g. `"ollama:nomic-embed-text"` |
   | `embed_documents(texts) -> list[list[float]]` | Vectors for code pieces. The provider adds its own prefix and cuts to its own length limit. |
   | `embed_query(text) -> list[float]` | A vector for a search question, with the provider's question prefix |
   | Errors | Raised as `EmbedderError`, so the existing fallback to keywords plus links keeps working |

   `load_embedder()` picks the class from a small table keyed by `provider`. A new provider is one new class and one line in that table. Prefixes and length limits are settings under that provider in `config/embedder.json`, not fixed in shared code. Every caller already uses only these methods, so no caller changes: `code_index.py`, `code_tools.py`, `code_source.py`, `orchestrator.py`, `eval_retrieval.py`.

3. **Vectors are stored per `model_key`, and their length is checked.**
   - `build_vectors`, `search_vectors` and `vector_count` use `model_key` instead of the bare model name.
   - The existing rows (`model = 'nomic-embed-text'`) are renamed once to `ollama:nomic-embed-text`. This is a plain SQL update, so nothing is re-embedded.
   - On load, every vector for a key must have the same length, and the query vector must match it. If not, an `EmbedderError` is raised, and search falls back to keywords plus links.

4. **Rules for switching models.**
   - A new model means embedding all pieces again: about 47 minutes on a laptop processor for 3,827 pieces with `nomic-embed-text`. It can be stopped and resumed, as now. Old vectors stay, so switching back costs nothing.
   - A model is adopted only after `scripts/eval_retrieval.py --method hybrid` is run with it, and it scores at least as well as the current one on the golden tickets. Search quality has to be shown, not assumed.
   - Each run records which search it used (`hybrid <model_key>` or `keywords+links` plus the reason) in its run record. A silent fallback then shows up.
   - A cloud provider (for example Gemini Embedding) needs the user's approval first. The 2026-10-26 decision was "local". It would also send code text to an outside service, so its key goes in `.env` as an `EMBED_*` setting.

## Consequences

**Better:**
- A code-specific model can be tried in Step 10, or Gemini Embedding if search falls short. Either is one class and a config change, measured with the same scoring script.
- Vectors from different providers, or of different lengths, cannot mix.
- A run that lost meaning search says so in its record.

**Costs:**
- A small change to `embedder.py` and `code_index.py`, plus a one-time rename of the existing vector rows.
- `tests/` and `scripts/smoke_test_step4.py` need updating for `model_key`.
- Each model tried costs a full embedding pass of tens of minutes, and its vectors make the index larger (about 3,827 × 768 × 4 bytes ≈ 12 MB per 768-length model).

**Unchanged:**
- The brain (D29) and embeddings stay separate. Switching `BRAIN=llm` / `slm` does not change search, so the two courses compare brains on the same search.
- Ollama for embeddings stays on the laptop. It is not the Kaggle SLM host.

## Alternatives considered

- **Leave it as is (Ollama only, no interface).** It works today, but every new model trial means editing shared code. The vector-mixing risk also stays.
- **Use a library (LangChain embeddings, sentence-transformers).** It would give many providers for free. But D1 rules out LangChain wrappers, and the dependency rules allow only the packages pinned in `requirements.txt`. sentence-transformers would also bring in PyTorch.
- **One database file per model instead of one key column.** This is cleaner to delete. But the keyword tables and links would be copied into each file, or a second database would be needed, and every caller would need to know which file to open.
- **Re-embed in place when the model changes (one set of vectors only).** This keeps the index small. But switching back costs another full pass, and two models cannot be compared side by side.

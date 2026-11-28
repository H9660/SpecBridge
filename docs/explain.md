# SpecBridge explained

SpecBridge takes a product manager's Jira ticket, reads the real code of five OpenMRS 3 frontend repos, and writes UAT test cases (steps and expected results) to a Confluence page.

The project has to work with two different "brains":
- a cloud LLM (Gemini), and
- small language models (SLMs) that we host ourselves.

Only the brain changes. The workflow, prompts, checks and tools are the same for both.

## How the SLMs are used

With `BRAIN=slm`, SpecBridge uses three small models. They run on a free Kaggle GPU (2× Tesla T4).

| Model | Size | Role |
|---|---|---|
| `qwen2.5-coder:14b` | 14B | Main model: understands the ticket, plans the work, writes and merges the test cases |
| `qwen2.5-coder:7b` | 7B | Worker search: picks the next tool call while a worker explores the code |
| `llama3.1:8b` | 8B | Reviewer: checks the finished test cases independently |

### Which model each stage uses

| Stage | Model | What the stage does |
|---|---|---|
| intake | none (plain code) | Reads the Jira ticket, removes secrets, flags text aimed at the AI |
| understand | `qwen2.5-coder:14b` | Turns the ticket into acceptance criteria and checks that the screens exist in the code |
| clarify | none (plain code) | Writes questions for the PM when the ticket cannot be tested |
| orchestrator | `qwen2.5-coder:14b` | Groups the criteria into tasks, one per worker |
| criterion worker: search | `qwen2.5-coder:7b` | Searches the code step by step (`search_code`, `read_file`, `grep`, `find_usages`) |
| criterion worker: write cases | `qwen2.5-coder:14b` | Writes test cases from the code the worker actually read |
| e2e worker | `7b` to search, `14b` to write | Same as a criterion worker, but builds end-to-end flows across criteria |
| merge | `qwen2.5-coder:14b` | Removes duplicate cases and tidies the plan |
| reviewer | `llama3.1:8b` | Checks each case against the code and the criteria, and can send weak criteria back for one more round |
| render, publish | none (plain code) | Builds the page and writes it to Confluence, then comments on the Jira ticket |

### Why this split

| Choice | Reason |
|---|---|
| A 7B model for search turns | A worker makes up to about 12 small decisions ("which tool next?"). A smaller model answers these in 2-4 s each. |
| A 14B model for writing | Writing grounded test cases from code is the hardest step, so it gets the strongest model. |
| A different model family for the reviewer | A reviewer from the same family tends to agree with the writer's mistakes. Llama checks Qwen's work. |
| No "thinking" models | No hidden reasoning that could run out of space and cut the answer. |
| All three fit on the GPU at once | About 19 GB in total across 2× T4 (16 GB each), so no model is unloaded and reloaded during a run. |

### The same stages on the cloud brain

For comparison, with `BRAIN=llm`:

| Role | SLM | Cloud LLM |
|---|---|---|
| Main | `qwen2.5-coder:14b` | `gemini-3.6-flash` |
| Worker search | `qwen2.5-coder:7b` | `gemini-3.5-flash-lite` |
| Reviewer | `llama3.1:8b` | `gemini-3.6-flash` |

The models for each role are set in [`config/brains.json`](../config/brains.json). Each stage asks for its role when it loads the brain, so switching brains changes one setting in `.env` and nothing in the code.

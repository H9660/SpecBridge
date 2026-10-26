# Autonomous Software Engineering — Implementation Plan

## 1. Problem Statement

Bridge the gap between high-level Jira product requirements and the actual codebase so an agent can understand intent, identify affected areas, and guide or execute the correct software changes with minimal human back-and-forth.

## 2. Target Architecture

The platform should be model-agnostic and support both Small Language Models (SLMs) and Large Language Models (LLMs) through an Adapter Pattern.

```text
Jira Ticket
    |
    v
Agent Orchestrator
    |
    +--> Planner
    +--> Retriever
    +--> Executor
    +--> Verifier
    +--> Reflection / Recovery
    |
    v
Model Router
    |
    +--> SLM Adapter --> Local model / Ollama
    |
    +--> LLM Adapter --> Cloud model / API
    |
    v
Tool Layer
    |
    +--> Code Knowledge Base
    +--> GitHub
    +--> Jira
    +--> Confluence
    +--> Test / Build / Lint tools
    |
    v
Human Approval
    |
    v
Pull Request / Merge
```

### Core architectural principle

Agents depend on a `ModelAdapter` interface, never directly on a specific model provider.

```text
Agent
  |
  v
ModelRouter
  |
  v
ModelAdapter
  |
  +--> OpenAIAdapter
  +--> OllamaAdapter
  +--> VLLMAdapter
  +--> Future adapters
```

This allows the same agent to use an SLM for inexpensive/simple tasks and escalate difficult tasks to an LLM without changing agent logic.

---

# 3. Jira Project Structure

Recommended Jira project: **ASE — Autonomous Software Engineering**

### Issue types

- Epic — major subsystem
- Story — user-visible capability
- Task — engineering implementation
- Spike — research / proof of concept
- Bug — defect
- Sub-task — work within a story
- Decision — architecture decision / ADR
- Experiment — model, retrieval, or agent evaluation

### Recommended labels

```text
agent-core
model-adapter
slm
llm
model-routing
rag
code-kb
github
jira
confluence
agent-tools
coding-agent
testing
security
observability
evaluation
human-in-loop
autonomy
```

---

# 4. Epics

| Epic | Name | Goal |
|---|---|---|
| E1 | Platform Foundation | Agent platform and infrastructure |
| E2 | Model Adapter Layer | SLM/LLM abstraction |
| E3 | Model Routing | Select the appropriate model for each task |
| E4 | Code Knowledge Base | Ground agents in the current codebase |
| E5 | Tool / Environment Layer | GitHub, Jira, Confluence, shell and test tools |
| E6 | Agent Runtime | Planning, execution, reflection and recovery |
| E7 | Software Engineering Agent | Autonomous coding workflow |
| E8 | Verification & Testing | Test generation, execution and repair |
| E9 | Human Approval & Governance | Safety and approval gates |
| E10 | Evaluation Framework | Measure quality, autonomy and efficiency |
| E11 | Observability & Security | Production readiness |
| E12 | Autonomous Workflow | End-to-end Jira → PR |

---

# 5. E1 — Platform Foundation

## E1-S1 — Define System Architecture

Tasks:
- Define service boundaries.
- Define agent runtime.
- Define model gateway.
- Define tool gateway.
- Define memory architecture.
- Define event/message model.
- Define configuration management.
- Create architecture diagram.
- Create architecture decision records.

Acceptance criteria:

```text
Given the platform architecture
When a new model provider is introduced
Then no agent business logic requires modification.
```

## E1-S2 — Create Agent Execution Framework

Core components:

```text
Agent
 ├── State
 ├── Planner
 ├── Executor
 ├── ToolRegistry
 ├── Memory
 ├── ModelAdapter
 └── Evaluator
```

Agent state should contain:

```text
task
goal
constraints
plan
current_step
observations
tool_results
artifacts
errors
evaluation
approval_state
```

## E1-S3 — Agent State Machine

```text
CREATED
   |
PLANNING
   |
RETRIEVING
   |
EXECUTING
   |
VERIFYING
   |
AWAITING_APPROVAL
   |
APPROVED
   |
COMPLETED
```

Failure path:

```text
ANY STATE
   |
RECOVERY
   |
RETRY / REPLAN / ESCALATE
```

The runtime must enforce limits such as maximum iterations, tool calls, cost and execution time.

---

# 6. E2 — Model Adapter Layer

## E2-S1 — Define ModelAdapter Interface

Recommended interface:

```text
ModelAdapter

+ generate(request)
+ stream(request)
+ structured_generate(request, schema)
+ tool_call(request, tools)
+ embed(request)
+ count_tokens(request)
+ health_check()
+ capabilities()
```

## E2-S2 — OpenAI Adapter

Example configuration:

```yaml
provider: openai
model: <configured-model>
```

## E2-S3 — Ollama Adapter

For local SLM execution:

```yaml
provider: ollama
model: qwen3:8b
endpoint: http://localhost:11434
```

## E2-S4 — vLLM Adapter

For future GPU/server deployment:

```text
VLLMModelAdapter
        |
        v
vLLM inference server
```

## E2-S5 — Model Capability Registry

Each model should expose capabilities such as:

```json
{
  "model": "qwen3:8b",
  "type": "slm",
  "context_window": 32768,
  "tool_calling": true,
  "structured_output": true,
  "reasoning": true,
  "vision": false
}
```

---

# 7. E3 — Model Routing

The agent should not use one model for every task.

```text
                  Task
                    |
                    v
              Model Router
              /           \
             v             v
           SLM             LLM
```

## E3-S1 — Task Classification

Classify tasks such as:

```text
CLASSIFY
EXTRACT
SUMMARIZE
RETRIEVE
RANK
GENERATE
PLAN
CODE
DEBUG
REVIEW
ARCHITECT
```

## E3-S2 — SLM Routing

Good candidates:

- Ticket classification
- Intent extraction
- Requirement extraction
- Code chunk summarization
- Metadata extraction
- Simple test generation
- Tool-result summarization

## E3-S3 — LLM Routing

Good candidates:

- Complex architecture reasoning
- Difficult debugging
- Large refactoring
- Ambiguous requirements
- Cross-repository reasoning
- Complex code generation
- Final review

## E3-S4 — Dynamic Escalation

Example:

```text
SLM
 |
 +-- high confidence --> execute
 |
 +-- low confidence --> escalate to LLM
```

The routing policy should consider confidence, task complexity, model capabilities, latency and cost.

---

# 8. E4 — Code Knowledge Base

The Code KB should be the primary code-grounding mechanism.

## E4-S1 — Repository Ingestion

```text
GitHub
  |
  v
Repository ingestion
  |
  v
Parser
  |
  v
AST
  |
  v
Chunker
```

## E4-S2 — AST-Aware Code Chunking

Chunk around:

- Functions
- Classes
- Components
- Hooks
- Services
- Routes
- Tests
- Configuration

Metadata should include:

```json
{
  "repo": "frontend-app",
  "branch": "main",
  "file": "src/components/DraftButton.tsx",
  "symbol": "DraftButton",
  "route": "/documents",
  "language": "typescript",
  "commit": "abc123"
}
```

## E4-S3 — Embedding Pipeline

```text
Code
 |
Embedding model
 |
Vector database
```

Store:

- Embedding
- Code
- Metadata
- Commit SHA
- Timestamp

## E4-S4 — Hybrid Retrieval

Combine:

```text
Vector search
+
BM25 / keyword search
+
Symbol search
+
Code relationships
```

Then rerank results.

## E4-S5 — Incremental Indexing

When a GitHub change is merged, re-index only affected files/symbols.

---

# 9. E5 — Tool / Environment Layer

Define a common tool contract:

```text
Tool
 ├── name
 ├── description
 ├── input_schema
 ├── execute()
 ├── permissions
 └── risk_level
```

Initial tools:

```text
search_code
read_file
write_file
search_github
create_branch
create_commit
create_pull_request

get_jira_ticket
update_jira_ticket
add_jira_comment

create_confluence_page
update_confluence_page

run_tests
run_linter
run_typecheck
run_build

git_diff
git_log
git_blame
```

Every tool should have explicit permissions and a risk classification.

---

# 10. E6 — Agent Runtime

The agent loop should evolve from the proposal's:

```text
Plan → Retrieve → Draft → Self-check
```

into:

```text
Understand
   |
Plan
   |
Retrieve
   |
Analyze
   |
Implement
   |
Test
   |
Review
   |
Fix
   |
Verify
   |
Human approval
```

## E6-S1 — Planner

Input:

```text
Jira ticket
repositories
constraints
```

Output:

```json
{
  "goal": "...",
  "steps": [
    {
      "id": 1,
      "action": "inspect component",
      "tools": ["search_code"]
    }
  ]
}
```

## E6-S2 — Tool Execution Loop

```text
Choose action
   |
Execute tool
   |
Observe result
   |
Update state
   |
Continue / replan
```

## E6-S3 — Reflection

After implementation:

```text
Implementation
      |
Reviewer
      |
Requirements?
Tests?
Security?
Regression?
Code quality?
      |
PASS / FAIL
```

---

# 11. E7 — Autonomous Software Engineering Agent

The initial proposal excludes writing/modifying code. This epic is the planned expansion from SpecBridge into autonomous software engineering.

## E7-S1 — Jira → Implementation Plan

Produce:

- Requirements
- Affected repositories
- Affected components
- Implementation plan
- Test plan
- Risk assessment

## E7-S2 — Branch Creation

```text
checkout main
   |
create branch
   |
implement
```

## E7-S3 — Code Modification

Allow the agent to read, edit and create files according to repository permissions.

## E7-S4 — Verification

Run:

```text
npm test
npm run lint
npm run typecheck
npm run build
```

Use repository-specific commands where appropriate.

## E7-S5 — Autonomous Repair Loop

```text
Implement
   |
Test
   |
FAIL
   |
Analyze failure
   |
Modify
   |
Test again
   |
PASS / ESCALATE
```

Set a maximum repair attempt count.

## E7-S6 — Pull Request Generation

Generate:

- PR title
- Description
- Summary
- Changed files
- Tests executed
- Risks
- Jira link

---

# 12. E8 — Verification & Testing

The agent must produce evidence, not merely code.

Verification should cover:

```text
Requirement verification
Unit tests
Integration tests
Type checking
Linting
Build
Static analysis
Diff review
Regression analysis
```

## E8-S1 — Acceptance Criterion Extraction

Map each acceptance criterion to:

```text
Requirement
   |
Implementation
   |
Test
   |
Evidence
```

## E8-S2 — Requirement Coverage Matrix

| Requirement | Code Evidence | Test | Result |
|---|---|---|---|
| AC1 | Implementation reference | Test reference | PASS/FAIL |
| AC2 | Implementation reference | Test reference | PASS/FAIL |
| AC3 | Implementation reference | Test reference | PASS/FAIL |

---

# 13. E9 — Human Approval & Governance

Start with controlled autonomy.

```text
L0 — Advisory
L1 — Read-only agent
L2 — Agent creates changes
L3 — Agent creates PR
L4 — Agent merges low-risk changes
L5 — Fully autonomous
```

Recommended rollout:

```text
L1 → L2 → L3
```

Require human approval for:

- Production deployment
- Database changes
- Security-sensitive changes
- Dependency upgrades
- Architecture changes
- Merge

---

# 14. E10 — Evaluation Framework

Track the following metrics.

| Metric | Formula |
|---|---|
| Requirement Coverage | `covered_requirements / total_requirements × 100` |
| Grounding Rate | `verified_references / total_references × 100` |
| Test Pass Rate | `passed_tests / executed_tests × 100` |
| Successful Task Rate | `successful_tasks / total_tasks × 100` |
| Human Acceptance Rate | `accepted_outputs / total_outputs × 100` |
| Escalation Rate | `LLM_escalations / total_tasks × 100` |
| SLM Utilization | `SLM_tasks / total_model_tasks × 100` |
| Average Cost | `total_model_cost / completed_tasks` |
| Autonomous Completion | `tasks_completed_without_human_intervention / total_tasks × 100` |

Create a benchmark using historical Jira tickets.

---

# 15. E11 — Observability & Security

Every agent execution should generate a trace containing:

```text
Run ID
Jira ID
Agent
Model
Model version
Prompt version
Tools used
Retrieval results
Tokens
Latency
Cost
Iterations
Errors
Final result
Human intervention
```

Example:

```text
RUN-18273

Model:
  qwen3:8b

Escalated:
  true

Escalation reason:
  confidence < threshold

Fallback:
  configured LLM

Tool calls:
  17

Iterations:
  4

Tests:
  143

Passed:
  143

Human intervention:
  0
```

Security requirements:

- Team-scoped access
- Least-privilege permissions
- Secrets never exposed to models
- Tool-level authorization
- Repository-level authorization
- Audit logs
- Risk-based tool policies

---

# 16. E12 — End-to-End Workflow

Target workflow:

```text
Jira Ticket
     |
     v
Requirement Extraction
     |
     v
Code KB Retrieval
     |
     v
Impact Analysis
     |
     v
Implementation Plan
     |
     v
Model Router
    / \
   v   v
 SLM  LLM
    \ /
     v
Coding Agent
     |
     v
Tests
     |
     +---- FAIL ---> Repair Loop
     |
     v
Code Review
     |
     v
PR Creation
     |
     v
Human Review
     |
     v
Merge
```

---

# 17. Initial Jira Backlog

Create these stories/tasks as the initial backlog:

```text
ASE-1   Define Autonomous Engineering Architecture
ASE-2   Define ModelAdapter Interface
ASE-3   Implement OpenAI Model Adapter
ASE-4   Implement Ollama Model Adapter
ASE-5   Implement Model Capability Registry
ASE-6   Implement Model Router
ASE-7   Implement SLM → LLM Escalation
ASE-8   Implement Agent State Machine
ASE-9   Implement Agent Tool Registry
ASE-10  Implement GitHub Read Tools
ASE-11  Implement Jira Read Tools
ASE-12  Implement Confluence Tools
ASE-13  Implement Repository Indexer
ASE-14  Implement AST-based Code Chunking
ASE-15  Implement Code Embedding Pipeline
ASE-16  Implement Vector Search
ASE-17  Implement Hybrid Code Retrieval
ASE-18  Implement Retrieval Reranking
ASE-19  Implement Agent Planner
ASE-20  Implement Agent Execution Loop
ASE-21  Implement Agent Reflection
ASE-22  Implement Jira Requirement Analyzer
ASE-23  Implement Code Impact Analyzer
ASE-24  Implement Implementation Planner
ASE-25  Implement Git Branch Creation
ASE-26  Implement Code Modification Tools
ASE-27  Implement Test Execution Tool
ASE-28  Implement Autonomous Repair Loop
ASE-29  Implement Code Review Agent
ASE-30  Implement Requirement-to-Test Mapping
ASE-31  Implement PR Generation
ASE-32  Implement Human Approval Gate
ASE-33  Implement Agent Run Tracing
ASE-34  Implement Token/Cost Tracking
ASE-35  Implement Agent Evaluation Harness
ASE-36  Build Historical Ticket Benchmark
ASE-37  Implement Security/Permission Policy
ASE-38  Implement Risk Classification
ASE-39  Implement End-to-End Jira → PR Workflow
ASE-40  Pilot Autonomous Engineering Agent
```

---

# 18. Delivery Plan

## Phase 1 — Foundation

**Sprint 1–2**

```text
E1 Platform
E2 Model Adapter
E5 Tool Layer
E11 Basic Observability
```

Deliverable:

> One agent can execute a task using either a local SLM or cloud LLM through the same interface.

## Phase 2 — Code Intelligence

**Sprint 3–4**

```text
E4 Code KB
GitHub integration
Hybrid retrieval
Repository indexing
```

Deliverable:

> Agent can reliably locate relevant code.

## Phase 3 — Agentic Reasoning

**Sprint 5–6**

```text
E6 Agent Runtime
Planner
Tool loop
Reflection
Memory
Model routing
```

Deliverable:

> Agent can investigate a Jira task autonomously.

## Phase 4 — Coding

**Sprint 7–9**

```text
E7 Software Engineering Agent
Git branch
Code changes
Testing
Repair
PR creation
```

Deliverable:

> Jira ticket → working PR.

## Phase 5 — Verification

**Sprint 10**

```text
E8 Verification
E10 Evaluation
```

Deliverable:

> Every PR has evidence that requirements were implemented and tested.

## Phase 6 — Governance

**Sprint 11**

```text
E9 Human approval
Security
Permissions
Risk levels
```

Deliverable:

> Agent cannot perform dangerous operations without approval.

## Phase 7 — Pilot

**Sprint 12**

Run the system against a representative set of historical Jira tickets and compare agent-assisted execution against the existing human workflow.

---

# 19. MVP Definition of Done

The MVP is complete when:

> Given a Jira ticket, the system can understand the requirement, retrieve relevant code, select an appropriate SLM/LLM through the adapter layer, produce an implementation plan, make changes in an isolated branch, run verification, repair failures, and create a PR, while maintaining a complete trace and requiring human approval before merge.

The complete MVP flow is:

```text
Jira
 ↓
Requirement extraction
 ↓
Code KB retrieval
 ↓
Impact analysis
 ↓
Plan
 ↓
Model routing
 ↓
SLM / LLM
 ↓
Code changes
 ↓
Tests
 ↓
Failure repair
 ↓
Review
 ↓
PR
 ↓
Human approval
 ↓
Merge
```

# 20. Key Architectural Principle

Do not build an "LLM agent."

Build an **agent runtime that happens to use models**.

That allows the system to move between:

```text
Local Qwen3 8B
       ↓
Qwen3 14B
       ↓
vLLM on GPU
       ↓
Cloud LLM
       ↓
Stronger LLM for complex reasoning
```

without rewriting the autonomous software-engineering system.


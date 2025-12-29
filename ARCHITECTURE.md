
# Multi-Agent LLM System Architecture for Local Context (Updated)

This document defines the architecture for a **terminal-first, multi-agent LLM system** that:

* Codes and refactors (with safe diffs and approvals)
* Does creative writing and conceptual work
* Extracts and uses information from local Obsidian vaults
* Builds scripts based on vault content
* Searches the internet via APIs and processes results with the same agent system

All while running in a **Neovim/tmux** environment with **plain-text + ANSI-colored** output.

---

## 0. Goals & Scope

**Primary capabilities:**

1. **Code & Systems Help**

   * Generate and refactor code
   * Suggest architecture improvements
   * Produce git-style diffs with explicit user approval before applying

2. **Creative & Conceptual Work**

   * Creative writing (stories, essays, blog posts)
   * Explanations, summaries, and conceptual analysis
   * Philosophy/psychology reasoning

3. **Vault-Aware Assistance (Obsidian)**

   * Read and query local Markdown content (Personal / Project vaults)
   * Build scripts, plans, and analyses based on vault content
   * Provide explicit source attribution

4. **External Web Search**

   * Call real web search APIs
   * Retrieve and summarize external information
   * Integrate external context into multi-agent workflows

5. **History & Feedback-Aware Behavior**

   * Persist session history and agent actions
   * Learn from user feedback and adjust prompts/configs safely over time

---

## 1. Core Knowledge Domains & Vaults

### 1.1 Core Knowledge Domains

The system is designed to assist across:

* Coding / Programming / Software Engineering
* Computer Science
* Mathematics
* Quantitative Finance
* Machine Learning
* Philosophy
* Psychology

### 1.2 Context Vault Structure

Local Markdown files are organized into two vaults:

1. **Personal Vault**

   * High-level, practical information
   * Personal thoughts, planning, tasks, organizing life
   * Gifts, vacations, writing ideas, journaling, personal work notes

2. **Project Vault**

   * Deep, technical, and academic knowledge
   * Personal interests, learning material, research notes
   * Career-related information
   * The Core Knowledge Domains listed above

### 1.3 RAG Vault Separation Policy

* **Each vault has its own vector store** (e.g., `personal_index`, `project_index`).
* Embeddings from both vaults are in the same space (same embedding model), but retrieval is **vault-scoped** first.
* Metadata for each chunk includes:

  * `vault` (personal/project)
  * `file_path`
  * `heading_path`
  * `created_at`, `updated_at`

---

## 2. Conceptual Architecture Overview

The system separates:

* **Orchestration & Planning**
* **Agent Execution**
* **Retrieval (RAG)**
* **LLM Provider Abstraction**
* **History & Feedback**
* **File I/O & Safe Write Layer**

### 2.1 Major Components

* **Orchestrator Layer**

  * Planner
  * Execution Manager
  * Synthesizer

* **Specialized Agents**

  * Code & Systems Agent
  * Quantitative Agent
  * Humanities Agent
  * Task & Planner Agent
  * Refinement Loop Agent
  * Critique Agent
  * Search Agent

* **Context & Storage**

  * RAG Service (per-vault vector stores)
  * SQLite Task Ledger (agent history, feedback, metadata)
  * Agent Context Files (per-agent Markdown instructions)

* **Runtime Abstractions**

  * `LLMProvider` interface (Gemini, OpenAI, Claude)
  * Embedding Provider
  * Web Search Provider

* **Interface**

  * Terminal-first CLI (Typer)
  * Neovim/tmux integration
  * ANSI-colored diffs, tables, and logs

### 2.2 Source Attribution Constraint

Every final output must explicitly state, for each significant piece of information, which source(s) it relied on:

* **Personal Vault**
* **Project Vault**
* **External Source** (web)
* **Model-only Reasoning** (no retrieved context)

This is enforced by the Critique Agent and Synthesizer.

---

## 3. Context Management & RAG

### 3.1 Data Ingestion (Indexing)

For each vault (`personal`, `project`):

1. **Loading**

   * Walk the configured directory
   * Load `.md` files
   * Optionally parse Obsidian-style frontmatter and headings

2. **Chunking**

   * Split Markdown into **semantically meaningful chunks**

     * Target: 500–1000 tokens
     * Overlap: 50–100 tokens
   * Respect headings; avoid splitting mid-sentence when possible

3. **Embedding**

   * Use a single embedding model (e.g., `text-embedding-004` from Gemini or an OpenAI embedding model)
   * Store:

     * `embedding` (vector)
     * `text`
     * `vault`, `file_path`, `heading_path`
     * `metadata` (tags, created_at, etc.)

4. **Vector Store**

   * One vector store per vault
   * Implementation options:

     * Chroma, FAISS, LanceDB, etc.
   * Metadata stored in SQLite as needed for auditing and cross-references

### 3.2 Retrieval Process

Given a user query:

1. **Vault Selection Heuristics**

   * Planner identifies probable vault:

     * Personal keywords → Personal Vault (e.g., “tasks”, “schedule”, “my journal”)
     * Technical/academic keywords → Project Vault (“gradient descent”, “PDE”, etc.)
   * User can override via CLI flags (`--vault personal|project|both`).

2. **Vector Search**

   * Embed the query
   * Perform similarity search on the chosen vault’s index
   * Optionally search both vaults if needed, tagging results by vault

3. **Context Assembly**

   * Select top-k chunks (e.g., k = 5–10)
   * Deduplicate overlapping info
   * Prepare “context bundle” with:

     * `text`
     * `vault`
     * `file_path`
     * `heading_path`

4. **No-Context Condition**

   * If no chunk exceeds a relevance threshold:

     * Orchestrator may:

       * Ask user whether to fallback to external Search Agent, or
       * Proceed without local context, marking output as **Model-only Reasoning**

---

## 4. Agent Memory, History & Self-Correction

### 4.1 Task Ledger (SQLite)

All interactions are logged in a **Task Ledger** stored in SQLite:

* `tasks` table

  * `task_id`
  * `user_query`
  * `created_at`
  * `status` (planned, running, completed, failed)

* `agent_steps` table

  * `step_id`
  * `task_id`
  * `agent_name`
  * `input`
  * `output`
  * `context_sources` (list of vault files / external URLs)
  * `timestamps`

* `feedback` table

  * `feedback_id`
  * `task_id`
  * `agent_name`
  * `rating` (numeric)
  * `comment`
  * `created_at`

### 4.2 Agent Message Schema

A unified message structure ensures consistency:

```json
{
  "task_id": "uuid",
  "from_agent": "orchestrator",
  "to_agent": "code_systems",
  "goal": "Refactor function X for readability",
  "context_chunks": [
    {
      "vault": "project",
      "file_path": "algorithms/trees.md",
      "heading_path": "## AVL Trees",
      "text": "..."
    }
  ],
  "user_constraints": {
    "language": "python",
    "no_external_packages": true
  },
  "data": {
    "code_snippet": "..."
  },
  "source": "Project Vault"
}
```

This schema can be implemented using Pydantic models.

### 4.3 Feedback Loop & Self-Correction

* User can approve/disapprove outputs.
* On disapproval, a structured feedback record is stored.
* A **meta-layer** process (Orchestrator or dedicated Meta Agent) can:

  * Analyze patterns in feedback
  * Suggest modifications to:

    * agent prompts, or
    * agent context Markdown files

#### 4.3.1 Prompt Patch Format (Safe Updates)

Agent context files are modified via **patches**, not raw overwrites:

```diff
--- agents/code_context.md
+++ agents/code_context.md
@@ -4,6 +4,7 @@
 - Always output diffs for code changes.
+ - Never introduce new external dependencies without explicit user permission.
```

Patch history is stored in SQLite to allow rollback or audit.

---

## 5. Agent Specialization & Orchestration

### 5.1 Orchestrator Layer (Decomposed)

Instead of a single monolithic Orchestrator, use three sub-roles:

1. **Planner**

   * Receive raw user query
   * Determine overall goal
   * Decide vault usage (Personal/Project/Both)
   * Break task into sub-tasks
   * Select appropriate agents per sub-task
   * Propose an execution plan

2. **Execution Manager**

   * Present plan to user for **pre-execution approval**
   * Once approved:

     * Dispatch tasks to agents
     * Manage inter-agent messaging
     * Enforce iteration caps (e.g., max 3 refinement loops unless user explicitly agrees)

3. **Synthesizer**

   * Collect outputs from all agents
   * Enforce **Source Attribution Constraint**
   * Ensure final output is coherent, de-duplicated, and user-aligned
   * Call Critique Agent before returning final answer if configured

### 5.2 Approval Gates

1. **Pre-Execution Approval (Plan Approval)**

   * Planner produces a human-readable plan:

     * Agents involved
     * Tasks per agent
     * Vaults to access
     * Whether external web search is needed
   * User must explicitly approve or modify the plan.

2. **In-Execution Approval (Code Diff Approval)**

   * Code & Systems Agent produces a git-style diff.
   * User must approve before the system applies changes to files.

3. **File Editing Permission (Safe Write Mode)**

   * All file edits happen via:

     * diff output → user approval → patch application
   * Agents never directly write arbitrary content to disk without the diff/approval cycle.

### 5.3 Specialized Agents

| Agent Name          | Domain                                   | Function                                                                                                                |
| ------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Code & Systems**  | Coding, CS, systems design               | Generate/refactor code, debug, explain algorithms. Always output git-style diffs for proposed changes.                  |
| **Quantitative**    | Math, Quant Finance, ML                  | Formal derivations, proofs, statistical modeling, ML reasoning, financial calculations.                                 |
| **Humanities**      | Philosophy, Psychology, Writing          | Conceptual analysis, ethical reasoning, frameworks, creative writing, summarizing dense texts.                          |
| **Task & Planner**  | Personal Vault                           | Task lists, schedules, personal notes, life planning (gifts, vacations, routines).                                      |
| **Refinement Loop** | Workflow/Iteration Control               | Manages refinement cycles. Routes external/search data to proper agents. Enforces iteration caps.                       |
| **Critique**        | QA across all agents                     | Validate outputs against user constraints and source attribution. May request revisions from other agents.              |
| **Search**          | External research (real web search APIs) | Calls web search APIs, retrieves content, preprocesses results, and sends structured data to relevant specialized agent |

### 5.4 Iteration Caps

* Default: **max 3 refinement iterations per task**.
* The Execution Manager or Refinement Agent must explicitly ask for user consent to exceed this.

---

## 6. LLM Provider & Tools Abstraction

### 6.1 LLM Providers

The system supports **multiple model providers** via a single abstraction:

* **Gemini**
* **OpenAI**
* **Anthropic Claude**

#### 6.1.1 `LLMProvider` Interface

A provider-agnostic interface (conceptually):

```python
class LLMResponse(BaseModel):
    content: str
    raw: Any | None = None

class LLMProvider(Protocol):
    def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> LLMResponse:
        ...
```

Concrete implementations:

* `GeminiProvider`
* `OpenAIProvider`
* `ClaudeProvider`

#### 6.1.2 Provider Selection

* Default provider is configured via env or config:

  * `LLM_PROVIDER=gemini|openai|claude`
* Per-agent overrides allowed in an agent config file (YAML/JSON):

```yaml
agents:
  code_systems:
    provider: "openai"
    model: "gpt-4.1"
  humanities:
    provider: "gemini"
    model: "gemini-1.5-pro"
  default_provider: "gemini"
```

### 6.2 Embedding Provider

* Similar abstraction for embeddings:

  * `EmbeddingProvider` interface
  * Underlying implementation can be Gemini or OpenAI embeddings
* RAG pipeline uses this provider exclusively.

### 6.3 Web Search Provider

The **Search Agent** uses a dedicated web search provider, e.g.:

* `SearchProvider` interface
* Concrete implementations:

  * `TavilySearchProvider`
  * `SerpAPISearchProvider`
  * Custom HTTP wrappers

The agent asks for:

* query
* optional filters (time, domain)
* max results

Results are normalized into a standard structure:

```json
{
  "title": "...",
  "url": "...",
  "snippet": "...",
  "content": "full or partial text if available"
}
```

---

## 7. Error Handling & Safety

### 7.1 Custom Exception Classes

Define domain-specific exceptions:

* `VaultAccessError`
* `RAGRetrievalError`
* `AgentCommunicationError`
* `LLMProviderError`
* `SearchProviderError`
* `PatchApplicationError`

### 7.2 RAG & Retrieval Failures

On retrieval failure or low similarity:

* Log the error
* Mark context as insufficient
* Offer user:

  * fallback to external Search Agent
  * or proceed with model-only reasoning (explicitly labeled)

### 7.3 LLM Errors

* On LLM provider error:

  * Log with provider name and operation
  * Optionally fallback to another provider (if configured)
  * Inform the user clearly

### 7.4 File I/O Safety

* Only allow modifications in **whitelisted directories**:

  * `personal_vault_path`
  * `project_vault_path`
  * optionally, a user-configurable code workspace
* Disallow:

  * editing binary files
  * editing certain extensions (e.g., `.env`, `.git`, secrets) unless explicitly allowed
* All changes must go through:

  * diff generation → user approval → patch application

---

## 8. Token & Context Management

* Use a **sliding window** over conversation history.
* For long-running sessions:

  * Summarize older context into compact “session summaries.”
* Limit per-call context:

  * Maximum number of RAG chunks
  * Maximum length of system + history messages
* Optionally introduce a **Summary Agent** responsible for:

  * Condensing long histories
  * Maintaining a high-level session state

---

## 9. Terminal-First Interface (Neovim/tmux)

### 9.1 CLI (Typer)

Core commands (examples):

* `ai chat "message"`
* `ai plan "high-level goal"` (shows Orchestrator plan for approval)
* `ai code refactor path/to/file.py --func my_function`
* `ai vault query "Explain my notes on X" --vault project`
* `ai search "latest research on Y"`

### 9.2 Output Formatting

* Plain text with **ANSI colors** for:

  * headings
  * error messages
  * diffs
  * tables

* Git-style diffs:

  ```diff
  diff --git a/file.py b/file.py
  --- a/file.py
  +++ b/file.py
  @@ -1,4 +1,6 @@
  -old line
  +new line
  ```

### 9.3 Neovim Integration

* Key mappings or commands that:

  * Send current buffer/selection to CLI
  * Receive diff or explanation
  * Show results in split or floating window
* Diff application via:

  * `git apply` style patches, or
  * Lua-based patch application

---

## 10. Technology Stack & Development Standards

| Component              | Recommendation           | Details & Justification                                                           |
| ---------------------- | ------------------------ | --------------------------------------------------------------------------------- |
| **Database**           | SQLite                   | Stores Task Ledger, metadata, feedback, patch history, and vector store metadata. |
| **Vector Store**       | FAISS / Chroma / LanceDB | For fast local embedding search; separate store per vault.                        |
| **Python Version**     | Python 3.12              | Modern syntax, performance improvements.                                          |
| **Testing**            | pytest                   | Standard Python test framework.                                                   |
| **Logging**            | loguru                   | Colorized, structured logging for terminal-first workflows.                       |
| **Config**             | pydantic-settings        | Type-safe environment configuration (`GEMINI_API_KEY`, etc.).                     |
| **Dependency Manager** | uv                       | Fast dependency resolution and environment management.                            |
| **CLI**                | Typer                    | Clean, composable CLI with help messages.                                         |
| **Error Handling**     | Custom exception classes | Predictable, structured error handling across the pipeline.                       |
| **Linting & Style**    | Ruff, mypy               | Linting, formatting, and static typing.                                           |
| **Pre-commit Hooks**   | `pre-commit` framework   | Run Ruff, mypy, and tests automatically on commit (especially for changed tests). |
| **Version Control**    | Git                      | Standard source control, separate from agent file-edit abilities.                 |
| **Deployment**         | Docker + Makefile        | Reproducible environment. `make build`, `make test`, `make run-cli`, etc.         |

---

This is now a cohesive, implementation-ready design spec that encodes:

* your original ideas,
* all the architectural suggestions, and
* your specific choices (Gemini/OpenAI/Claude, safe write mode, real external search).

In the **next step**, I’ll use this document as the blueprint to set up:

* the initial project layout,
* settings & provider abstractions,
* the CLI skeleton,
* and the first minimal vertical slice (one command talking to your chosen provider).


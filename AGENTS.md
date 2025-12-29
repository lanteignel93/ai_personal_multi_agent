# AGENTS.md — Multi-Agent LLM System (Terminal-First)

## Purpose

This repository implements a terminal-first, multi-provider (Gemini/OpenAI/Claude) multi-agent system that:

* uses local Obsidian Markdown vaults via RAG,
* supports safe code changes via diffs + explicit approval,
* can optionally perform real web search via API and process results through agents,
* logs all actions to a local SQLite task ledger.

These instructions define the working contract for Codex when editing this repo.

---

## Operating Principles (Read First)

### 1) Terminal-first UX

* All user-facing output must work in a tty (Kitty/tmux).
* Prefer plain text, ANSI color, ASCII/Unicode tables.
* No web UI assumptions.

### 2) Safety: diffs + approval for any change

* Any non-trivial modification must be presented as a **git-style diff** first.
* Do not apply patches or rewrite files without an explicit user approval step in the workflow.
* When unsure, propose a small diff and ask for confirmation.

### 3) Local-first + source attribution

* When implementing “answering” flows, prefer local vault retrieval (Personal/Project) before external sources.
* Any user-facing synthesis must include source attribution categories:
* Personal Vault
* Project Vault
* External Source
* Model-only reasoning (if no retrieval/search used)

### 4) Keep changes incremental

* Make the smallest coherent change that advances the current milestone.
* Avoid large refactors unless requested.

### 5) Context Hygiene

* **Pollution Check:** Before starting a Plan, assume your context window is "dirty." explicitly list the 2-3 files you need to load to understand the current problem.
* **State Anchoring:** Clearly state if you are in `PLANNING_MODE` (high-level, low detail) or `CODING_MODE` (low-level, high detail). Do not mix them.

### 6) Context "Priming" (Positive Reinforcement)

* **Problem:** LLMs struggle with negative constraints ("Do not do X").
* **Solution:** When starting a complex task (like a Migration), first read a *successful* prior example from the `tasks.db` or `MEMORY.md`.
* **Reasoning:** Pattern-matching a "Gold Standard" example is more reliable than following a list of restrictions.

### 7) Context Bankruptcy

* If you find yourself looping or hallucinating, declare "Context Bankruptcy."
* **Action:** Propose clearing the current conversation history while preserving the `Plan` state.
* **Why:** "Needle in a haystack" degradation happens after ~10-15 turns. It is better to reset than to persist with a polluted window.

---

## Project Milestones (Build Order)

Implement in thin vertical slices:

**V0 — Spine**

* Typer CLI skeleton
* provider abstraction (Gemini/OpenAI/Claude)
* SQLite task ledger logging
* `ai chat "..."` works end-to-end

**V1 — Vault Query (RAG-lite)**

* `ai vault query "..." --vault personal|project|both`
* top-k retrieval + attribution

**V1.5 — Shared Fact Store (Active Memory)**

* Implement a `facts` table in SQLite (separate from the task ledger).
* Schema: `(key, value, source_agent, confidence_score)`.
* Allow agents to `set_fact("api_limit", "50")` and `get_fact("api_limit")`.
* This prevents agents from re-discovering the same constraints repeatedly.

**V2 — Plan Approval**

* `ai plan "..."` prints a plan and requires explicit approval before execution

**V3 — Safe Write Diff Loop**

* `ai code propose <path> "<goal>"`
* outputs diff, waits for approval, applies patch if approved, logs everything

**V4 — Real Web Search Agent**

* `ai search "..."` via a search API provider
* normalized results + attribution

Keep PR/commit scope aligned to the current milestone.

---

## Repository Conventions

### Python & Tooling

* Python: 3.12+
* CLI: Typer
* Config: pydantic-settings (.env supported)
* Logging: loguru (structured, readable)
* Lint/format: Ruff
* Types: mypy (where practical)
* Tests: pytest

### Architecture Documents

These are source-of-truth references:

* `ARCHITECTURE.md` (formal spec)
* `ARCHITECTURE_HYBRID.md` (readable spec)
If implementation choices conflict with these docs, flag it and propose an adjustment.

---

## Coding Standards (Enforced)

### General Standards

* Prefer small modules with clear responsibilities.
* Use explicit, typed interfaces for providers (`LLMProvider`, `SearchProvider`).
* Avoid “magic” globals; configuration should flow from settings.
* Errors: define custom exception classes; do not swallow exceptions silently.
* Logging must not leak secrets (API keys) or sensitive vault content.

### Modern Tooling (uv)

*From simple-modern-uv template*

* **Package Management:**
* **Strictly use `uv**` for all dependency management.
* ❌ NEVER use `pip install`, `poetry`, or `venv` directly.
* ✅ Use: `uv add <package>`, `uv sync`, `uv run <script>`.


* **Reproducibility:**
* Do not rely on global Python. Always execute code via `uv run`.
* *Example:* `uv run pytest` instead of `pytest`.



### Tech Stack Standards (Pydantic & Python)

*From Cole Medin’s Pydantic AI Protocol*

* **Pydantic V2 Strictness:**
* NEVER use `.dict()`; use `.model_dump()`.
* NEVER use `.parse_obj()`; use `.model_validate()`.
* Use `field_validator` (mode='before'/'after') instead of the old `validator`.
* Always set `model_config = ConfigDict(extra='forbid')` for strict agent schemas.


* **Type Safety:**
* Use `typing.Annotated` for all Tool arguments.
* Prefer `pathlib.Path` over `str` for file paths.
* No `Any` types unless absolutely necessary.


* **Agentic Patterns:**
* **Tool Definitions:** Every function exposed to an agent MUST have a docstring that describes *when* to use it, not just *how*.
* **Return Values:** Tools should return structured text or Pydantic models, not complex objects.



---

## Safe File I/O Rules

* Do not read/write outside configured whitelisted directories:
* vault paths
* project workspace


* Never modify `.env`, secrets, SSH keys, or `.git` internals without asking for approval.
* For patch application:
* produce diff → request approval → apply patch → verify → log.



---

## Planning & Execution Protocol

When tasks are non-trivial, follow this protocol:

1. **Plan (The "PRP" Phase)**
*Do not write code yet. Output a Product Requirement Prompt (PRP) block:*

* **Objective:** One clear sentence on the goal.
* **Context Isolation:** Explicitly list the *only* files you need to read to execute this (e.g., "Read `src/main.py`, ignore `tests/old_tests`").
* **Validation Gates:** Define the specific "Exit Criteria" that *must* pass.
* *Example:* "New function must pass `pytest tests/test_new_feature.py`."
* *Example:* "Run `mypy` and ensure 0 errors."


* **Atomic Steps:** Numbered list of changes.
* **Stop:** Ask for user approval.
* **Context Reset Instruction:** *Once approved, treat this PRP as the primary source of truth. Ignore previous brainstorming tangents.*

2. **Implement**

* Make incremental edits.
* Keep changes testable.
* Prefer adding tests for new logic.

3. **Verify (Standard Commands)**
*Use these standard commands to verify your work. ALWAYS use `uv run`.*

* **Unit Tests:** `uv run pytest tests/unit`
* **Integration:** `uv run pytest tests/integration`
* **Linting:** `uv run ruff check .`
* **Type Check:** `uv run mypy .`
* **Dry Run:** `uv run python -m src.main chat "test" --dry-run`
* If you cannot run commands, state exactly what the user should run.

4. **Review**

* Provide a concise diff summary and any tradeoffs.
* **Context Preservation:** If a file is too large to read, ask the user to run `ai vault query` to get a summarized snippet rather than summarizing it yourself.
* **Memory:** Update `MEMORY.md` if a major architectural decision was made (e.g. "We chose Schema X over Y because...").

---

## Review Guidelines (What to Look For)

Before finalizing changes, verify:

* No secrets or PII logged.
* Provider abstraction is respected (no provider-specific calls in agent logic).
* Diff/approval workflows exist for file modifications.
* Source attribution categories are preserved end-to-end.
* SQLite task ledger records tasks/steps/patches.
* CLI commands remain ergonomic for tmux/Neovim use.

---

## Commands (Expected)

Codex should prefer implementing these CLI entrypoints:

* `ai chat "<prompt>"`
* `ai plan "<goal>"`
* `ai vault query "<query>" --vault personal|project|both`
* `ai code propose <path> "<goal>"`
* `ai code apply <patch_id | patch_file>` (approval-gated)
* `ai search "<query>"` (real search API)

---

## Provider Configuration Contract

All provider selection is config-driven:

* `LLM_PROVIDER=gemini|openai|claude`
* keys via environment:
* `GEMINI_API_KEY`
* `OPENAI_API_KEY`
* `ANTHROPIC_API_KEY` (or `CLAUDE_API_KEY` if preferred—choose one and standardize)



Codex: do not hardcode keys; do not print keys.

---

## Definition of Done (Per Change)

A change is done when:

* CLI behavior is demonstrable via a concrete command example.
* The change is logged in SQLite where applicable.
* Tests added or updated for new logic (when reasonable).
* Output remains terminal-friendly.
* Source attribution requirements are not broken.

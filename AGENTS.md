# AGENTS.md — Multi-Agent LLM System (Terminal-First)

## Purpose
This repository implements a terminal-first, multi-provider (Gemini/OpenAI/Claude) multi-agent system that:
- uses local Obsidian Markdown vaults via RAG,
- supports safe code changes via diffs + explicit approval,
- can optionally perform real web search via API and process results through agents,
- logs all actions to a local SQLite task ledger.

These instructions define the working contract for Codex when editing this repo.

---

## Operating Principles (Read First)

### 1) Terminal-first UX
- All user-facing output must work in a tty (Kitty/tmux).
- Prefer plain text, ANSI color, ASCII/Unicode tables.
- No web UI assumptions.

### 2) Safety: diffs + approval for any change
- Any non-trivial modification must be presented as a **git-style diff** first.
- Do not apply patches or rewrite files without an explicit user approval step in the workflow.
- When unsure, propose a small diff and ask for confirmation.

### 3) Local-first + source attribution
- When implementing “answering” flows, prefer local vault retrieval (Personal/Project) before external sources.
- Any user-facing synthesis must include source attribution categories:
  - Personal Vault
  - Project Vault
  - External Source
  - Model-only reasoning (if no retrieval/search used)

### 4) Keep changes incremental
- Make the smallest coherent change that advances the current milestone.
- Avoid large refactors unless requested.

---

## Project Milestones (Build Order)
Implement in thin vertical slices:

**V0 — Spine**
- Typer CLI skeleton
- provider abstraction (Gemini/OpenAI/Claude)
- SQLite task ledger logging
- `ai chat "..."` works end-to-end

**V1 — Vault Query (RAG-lite)**
- `ai vault query "..." --vault personal|project|both`
- top-k retrieval + attribution

**V2 — Plan Approval**
- `ai plan "..."` prints a plan and requires explicit approval before execution

**V3 — Safe Write Diff Loop**
- `ai code propose <path> "<goal>"`
- outputs diff, waits for approval, applies patch if approved, logs everything

**V4 — Real Web Search Agent**
- `ai search "..."` via a search API provider
- normalized results + attribution

Keep PR/commit scope aligned to the current milestone.

---

## Repository Conventions

### Python & Tooling
- Python: 3.12+
- CLI: Typer
- Config: pydantic-settings (.env supported)
- Logging: loguru (structured, readable)
- Lint/format: Ruff
- Types: mypy (where practical)
- Tests: pytest

### Architecture Documents
These are source-of-truth references:
- `ARCHITECTURE.md` (formal spec)
- `ARCHITECTURE_HYBRID.md` (readable spec)
If implementation choices conflict with these docs, flag it and propose an adjustment.

---

## Coding Standards (Enforced)
- Prefer small modules with clear responsibilities.
- Use Pydantic models for any structured agent messages/state.
- Use explicit, typed interfaces for providers:
  - `LLMProvider` (Gemini/OpenAI/Claude)
  - `EmbeddingProvider`
  - `SearchProvider`
- Avoid “magic” globals; configuration should flow from settings.
- Errors: define custom exception classes; do not swallow exceptions silently.
- Logging must not leak secrets (API keys) or sensitive vault content.

---

## Safe File I/O Rules
- Do not read/write outside configured whitelisted directories:
  - vault paths
  - project workspace
- Never modify `.env`, secrets, SSH keys, or `.git` internals.
- For patch application:
  - produce diff → request approval → apply patch → verify → log.

---

## Planning & Execution Protocol
When tasks are non-trivial, follow this protocol:

1) **Plan**
- Summarize the goal.
- Identify which milestone it impacts.
- Propose a short step-by-step plan.
- List files that will change.
- Ask for approval (or proceed only if user explicitly asked you to implement immediately).

2) **Implement**
- Make incremental edits.
- Keep changes testable.
- Prefer adding tests for new logic.

3) **Verify**
- Run formatting/linting/tests where applicable.
- If you cannot run commands, state what should be run.

4) **Review**
- Provide a concise diff summary and any tradeoffs.
- Ensure attribution plumbing exists for any user-facing responses.

---

## Review Guidelines (What to Look For)
Before finalizing changes, verify:
- No secrets or PII logged.
- Provider abstraction is respected (no provider-specific calls in agent logic).
- Diff/approval workflows exist for file modifications.
- Source attribution categories are preserved end-to-end.
- SQLite task ledger records tasks/steps/patches.
- CLI commands remain ergonomic for tmux/Neovim use.

---

## Commands (Expected)
Codex should prefer implementing these CLI entrypoints:

- `ai chat "<prompt>"`
- `ai plan "<goal>"`
- `ai vault query "<query>" --vault personal|project|both`
- `ai code propose <path> "<goal>"`
- `ai code apply <patch_id | patch_file>` (approval-gated)
- `ai search "<query>"` (real search API)

---

## Provider Configuration Contract
All provider selection is config-driven:
- `LLM_PROVIDER=gemini|openai|claude`
- keys via environment:
  - `GEMINI_API_KEY`
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY` (or `CLAUDE_API_KEY` if preferred—choose one and standardize)

Codex: do not hardcode keys; do not print keys.

---

## Definition of Done (Per Change)
A change is done when:
- CLI behavior is demonstrable via a concrete command example.
- The change is logged in SQLite where applicable.
- Tests added or updated for new logic (when reasonable).
- Output remains terminal-friendly.
- Source attribution requirements are not broken.



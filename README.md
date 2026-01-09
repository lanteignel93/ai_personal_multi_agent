# Multi-Agent LLM System

Terminal-first, multi-provider agent system with local vault retrieval, safe diffs, and approvals.

## Quick start

```bash
uv venv
uv pip install -e ".[dev]"
```

Run the CLI:

```bash
uv run ai chat "hello world"
```

## Configuration

Copy `.env.example` to `.env` and edit as needed:

```bash
cp .env.example .env
```

Key variables:

- `LLM_PROVIDER=echo|gemini|openai|claude`
- `AI_LEDGER_PATH=/absolute/path/to/ledger-repo/task_ledger.db`
- `AI_LOG_LEVEL=INFO`
- `EMBEDDING_PROVIDER=gemini`
- `GEMINI_EMBEDDING_MODEL=text-embedding-004`
- `PERSONAL_VAULT_PATH=/home/laurent/obsidian/Personal`
- `PROJECT_VAULT_PATH=/home/laurent/obsidian/Project`
- `VECTOR_INDEX_ROOT=/home/laurent/obsidian/ai_vector_idx`

## Development

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

## Vaults (V1)

Build indexes:

```bash
uv run ai vault index --vault both --mode update-all
```

Query indexes:

```bash
uv run ai vault query "your query" --vault personal --top-k 5
```

## CI

CI runs Ruff and pytest on Ubuntu via GitHub Actions.

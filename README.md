# Multi-Agent LLM System

Terminal-first, multi-provider agent system with local vault retrieval, safe diffs, and approvals.

## Quick start

```bash
uv pip install -e ".[dev]"
```

Run the CLI:

```bash
ai chat "hello world"
```

## Development

```bash
ruff check .
ruff format .
pytest
```

## CI

CI runs Ruff and pytest on Ubuntu via GitHub Actions.

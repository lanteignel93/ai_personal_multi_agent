import re
import textwrap
from pathlib import Path
from time import perf_counter

import typer
from loguru import logger

from .ledger import TaskLedger
from .logging import configure_logging
from .providers.base import get_provider
from .providers.embeddings import get_embedding_provider
from .settings import get_settings
from .vault.indexer import index_vault
from .vault.retriever import query_vault_index

app = typer.Typer(
    add_completion=False,
    help="Terminal-first multi-agent CLI",
    epilog='Examples:\n  ai chat "hello"',
)
vault_app = typer.Typer(help="Vault operations")
app.add_typer(vault_app, name="vault")

PATH_CONTAINS_OPTION = typer.Option(
    None, help="Only include results whose path contains these substrings."
)
PATH_EXCLUDES_OPTION = typer.Option(
    None, help="Exclude results whose path contains these substrings."
)


@app.callback()
def main() -> None:
    """Root CLI group."""
    configure_logging()
    return


@app.command(help="Send a prompt to the configured LLM provider.")
def chat(prompt: str = typer.Argument(..., help="User prompt to send")) -> None:
    if not prompt.strip():
        raise typer.BadParameter("prompt must be non-empty")
    ledger = TaskLedger.from_env()
    task_id = ledger.log_task(prompt, command="chat")
    log = logger.bind(task_id=task_id, command="chat")
    try:
        provider = get_provider()
        log = log.bind(provider=provider.name)
        log.info("chat request received")
        response = provider.chat(prompt)
        ledger.log_step(task_id, provider.name, prompt, response)
        ledger.complete_task(task_id, status="completed")
        log.info("chat response stored")
        typer.echo(response)
    except Exception as exc:
        ledger.complete_task(task_id, status="failed", error=str(exc))
        log.exception("chat request failed")
        raise


@vault_app.command("index", help="Build or update a vault index.")
def vault_index(
    vault: str = typer.Option(
        "both", help="Vault to index: personal, project, or both."
    ),
    mode: str = typer.Option(
        "update-all", help="Index mode: rebuild, update-all, or update-new."
    ),
    max_words: int = typer.Option(800, help="Max words per chunk."),
    overlap_words: int = typer.Option(100, help="Overlap words between chunks."),
    batch_size: int = typer.Option(16, help="Embedding batch size."),
    cleanup_deleted: bool = typer.Option(
        False, help="Remove indexed files that no longer exist."
    ),
) -> None:
    start = perf_counter()
    settings = get_settings()
    provider = get_embedding_provider()
    ledger = TaskLedger.from_env()
    task_id = ledger.log_task(f"vault index {vault}", command="vault-index")
    log = logger.bind(task_id=task_id, command="vault-index", vault=vault)

    vault_map = {
        "personal": settings.personal_vault_path,
        "project": settings.project_vault_path,
    }
    index_root = settings.vector_index_root
    if index_root is None:
        raise typer.BadParameter("VECTOR_INDEX_ROOT is not set.")

    targets = ["personal", "project"] if vault == "both" else [vault]
    total_chunks = 0
    try:
        for target in targets:
            path = vault_map.get(target)
            if path is None:
                raise typer.BadParameter(f"{target} vault path is not set.")
            index_path = index_root / f"{target}.sqlite3"
            log = log.bind(vault=target)
            chunk_count = index_vault(
                target,
                path,
                index_path,
                provider,
                mode=mode,
                max_words=max_words,
                overlap_words=overlap_words,
                batch_size=batch_size,
                cleanup_deleted=cleanup_deleted,
            )
            total_chunks += chunk_count
            log.info("vault indexed")
        ledger.log_step(
            task_id,
            provider.name,
            f"index vault={vault} mode={mode} cleanup_deleted={cleanup_deleted}",
            f"chunks_indexed={total_chunks}",
            duration_ms=int((perf_counter() - start) * 1000),
        )
        ledger.complete_task(task_id, status="completed")
        elapsed = perf_counter() - start
        typer.echo(f"Indexed {total_chunks} chunks into {index_root} in {elapsed:.2f}s")
    except Exception as exc:
        ledger.complete_task(task_id, status="failed", error=str(exc))
        log.exception("vault indexing failed")
        raise


@vault_app.command("query", help="Query a vault index.")
def vault_query(
    query: str = typer.Argument(..., help="Query to search for."),
    vault: str = typer.Option(
        "both", help="Vault to query: personal, project, or both."
    ),
    top_k: int = typer.Option(5, help="Number of results per vault."),
    answer: bool = typer.Option(
        True, "--answer/--no-answer", help="Synthesize an answer with citations."
    ),
    exclude_templates: bool = typer.Option(
        True,
        "--exclude-templates/--include-templates",
        help="Exclude templates from results.",
    ),
    path_contains: list[str] = PATH_CONTAINS_OPTION,
    path_excludes: list[str] = PATH_EXCLUDES_OPTION,
) -> None:
    start = perf_counter()
    if not query.strip():
        raise typer.BadParameter("query must be non-empty")
    settings = get_settings()
    provider = get_embedding_provider()
    llm_provider = get_provider()
    ledger = TaskLedger.from_env()
    task_id = ledger.log_task(query, command="vault-query")
    log = logger.bind(task_id=task_id, command="vault-query", vault=vault)

    vault_map = {
        "personal": settings.personal_vault_path,
        "project": settings.project_vault_path,
    }
    index_root = settings.vector_index_root
    if index_root is None:
        raise typer.BadParameter("VECTOR_INDEX_ROOT is not set.")

    targets = ["personal", "project"] if vault == "both" else [vault]
    all_results: list[str] = []
    try:
        for target in targets:
            path = vault_map.get(target)
            if path is None:
                raise typer.BadParameter(f"{target} vault path is not set.")
            index_path = index_root / f"{target}.sqlite3"
            results = query_vault_index(
                target, index_path, query, provider, top_k=top_k
            )
            results = _filter_results(
                results,
                exclude_templates=exclude_templates,
                path_contains=path_contains or [],
                path_excludes=path_excludes or [],
            )
            typer.echo(f"Results ({target}):")
            for idx, item in enumerate(results, start=1):
                heading = f"#{item.heading_path}" if item.heading_path else ""
                short_path = _shorten_path(item.file_path, path)
                typer.echo(f"{idx}. [{item.score:.3f}] {short_path}{heading}")
                snippet = _clean_snippet(item.text)
                typer.echo(
                    textwrap.fill(
                        snippet,
                        width=100,
                        subsequent_indent="   ",
                        initial_indent="   ",
                    )
                )
            all_results.append(target)
            if answer and results:
                typer.echo("\nAnswer:")
                prompt = _build_answer_prompt(query, results)
                response = llm_provider.chat(prompt)
                typer.echo(textwrap.fill(response, width=100))
                ledger.log_step(
                    task_id,
                    llm_provider.name,
                    f"answer vault={vault}",
                    response,
                )
        ledger.log_step(
            task_id,
            provider.name,
            f"query vault={vault}",
            f"results_vaults={','.join(all_results)}",
            duration_ms=int((perf_counter() - start) * 1000),
        )
        ledger.complete_task(task_id, status="completed")
        elapsed = perf_counter() - start
        typer.echo(f"Sources: {', '.join(_vault_labels(all_results))}")
        typer.echo(f"Elapsed: {elapsed:.2f}s")
    except Exception as exc:
        ledger.complete_task(task_id, status="failed", error=str(exc))
        log.exception("vault query failed")
        raise


def _vault_labels(vaults: list[str]) -> list[str]:
    labels = []
    if "personal" in vaults:
        labels.append("Personal Vault")
    if "project" in vaults:
        labels.append("Project Vault")
    return labels


def _shorten_path(file_path: str, vault_path: Path) -> str:
    try:
        return str(Path(file_path).relative_to(vault_path))
    except ValueError:
        return Path(file_path).name


def _clean_snippet(text: str) -> str:
    cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:300]


def _filter_results(
    results,
    *,
    exclude_templates: bool,
    path_contains: list[str],
    path_excludes: list[str],
):
    filtered = []
    for item in results:
        path_lower = item.file_path.lower()
        if exclude_templates and (
            "template" in path_lower or "/templates/" in path_lower
        ):
            continue
        if path_contains and not any(p.lower() in path_lower for p in path_contains):
            continue
        if path_excludes and any(p.lower() in path_lower for p in path_excludes):
            continue
        filtered.append(item)
    return filtered


def _build_answer_prompt(query: str, results) -> str:
    lines = [
        f"Question: {query}",
        "Use only the context below and cite sources as [n].",
    ]
    for idx, item in enumerate(results, start=1):
        snippet = _clean_snippet(item.text)
        lines.append(f"[{idx}] {snippet}")
    lines.append("Answer in 3-5 bullets, with citations.")
    return "\n".join(lines)

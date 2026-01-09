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


@vault_app.command("index", help="Build or rebuild a vault index.")
def vault_index(
    vault: str = typer.Option(
        "both", help="Vault to index: personal, project, or both."
    ),
    rebuild: bool = typer.Option(True, help="Rebuild the index from scratch."),
    max_words: int = typer.Option(800, help="Max words per chunk."),
    overlap_words: int = typer.Option(100, help="Overlap words between chunks."),
    batch_size: int = typer.Option(16, help="Embedding batch size."),
) -> None:
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
                rebuild=rebuild,
                max_words=max_words,
                overlap_words=overlap_words,
                batch_size=batch_size,
            )
            total_chunks += chunk_count
            log.info("vault indexed")
        ledger.log_step(
            task_id,
            provider.name,
            f"index vault={vault}",
            f"chunks_indexed={total_chunks}",
        )
        ledger.complete_task(task_id, status="completed")
        typer.echo(f"Indexed {total_chunks} chunks into {index_root}")
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
) -> None:
    if not query.strip():
        raise typer.BadParameter("query must be non-empty")
    settings = get_settings()
    provider = get_embedding_provider()
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
            typer.echo(f"Results ({target}):")
            for idx, item in enumerate(results, start=1):
                heading = f"#{item.heading_path}" if item.heading_path else ""
                typer.echo(f"{idx}. [{item.score:.3f}] {item.file_path}{heading}")
                snippet = item.text.replace("\n", " ")[:200]
                typer.echo(f"   {snippet}")
            all_results.append(target)
        ledger.log_step(
            task_id,
            provider.name,
            f"query vault={vault}",
            f"results_vaults={','.join(all_results)}",
        )
        ledger.complete_task(task_id, status="completed")
        typer.echo(f"Sources: {', '.join(_vault_labels(all_results))}")
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

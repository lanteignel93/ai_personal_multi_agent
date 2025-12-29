import typer
from loguru import logger

from .ledger import TaskLedger
from .logging import configure_logging
from .providers.base import get_provider

app = typer.Typer(
    add_completion=False,
    help="Terminal-first multi-agent CLI",
    epilog='Examples:\n  ai chat "hello"',
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

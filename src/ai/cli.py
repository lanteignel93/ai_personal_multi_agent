import typer

from .ledger import TaskLedger
from .providers.base import get_provider

app = typer.Typer(add_completion=False, help="Terminal-first multi-agent CLI")


@app.callback()
def main() -> None:
    """Root CLI group."""
    return


@app.command()
def chat(prompt: str = typer.Argument(..., help="User prompt to send")) -> None:
    """Send a prompt to the configured LLM provider."""
    ledger = TaskLedger.from_env()
    task_id = ledger.log_task(prompt)
    provider = get_provider()
    response = provider.chat(prompt)
    ledger.log_step(task_id, provider.name, prompt, response)
    typer.echo(response)

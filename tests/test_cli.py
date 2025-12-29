from typer.testing import CliRunner

from ai.cli import app

runner = CliRunner()


def test_chat_echo(tmp_path) -> None:
    ledger_path = tmp_path / "ledger.db"
    result = runner.invoke(
        app,
        ["chat", "hello"],
        env={"AI_LEDGER_PATH": str(ledger_path)},
    )
    assert result.exit_code == 0
    assert "ECHO: hello" in result.stdout


def test_chat_rejects_empty_prompt(tmp_path) -> None:
    ledger_path = tmp_path / "ledger.db"
    result = runner.invoke(
        app,
        ["chat", "   "],
        env={"AI_LEDGER_PATH": str(ledger_path)},
    )
    assert result.exit_code != 0
    assert "prompt must be non-empty" in result.output

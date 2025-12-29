from pathlib import Path

from ai.settings import get_settings


def test_settings_load_from_dotenv(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "LLM_PROVIDER=gemini\nAI_LEDGER_PATH=/tmp/ledger.db\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("AI_LEDGER_PATH", raising=False)

    settings = get_settings()

    assert settings.llm_provider == "gemini"
    assert settings.ai_ledger_path == Path("/tmp/ledger.db")

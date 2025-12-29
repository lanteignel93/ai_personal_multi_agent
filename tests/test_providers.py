import pytest

from ai.errors import ProviderNotConfiguredError
from ai.providers.base import get_provider


def test_provider_requires_key(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    provider = get_provider()
    with pytest.raises(ProviderNotConfiguredError):
        provider.chat("hello")

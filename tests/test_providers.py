import pytest

from ai.errors import ProviderNotConfiguredError, ProviderNotImplementedError
from ai.providers.base import get_provider


def test_provider_requires_key(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    provider = get_provider()
    with pytest.raises(ProviderNotConfiguredError):
        provider.chat("hello")


def test_provider_invalid_name(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "not-a-provider")

    with pytest.raises(ProviderNotImplementedError):
        get_provider()


def test_provider_rejects_empty_setting(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "   ")

    with pytest.raises(ProviderNotConfiguredError):
        get_provider()

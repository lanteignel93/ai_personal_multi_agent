from typing import Protocol

from ..errors import ProviderNotConfiguredError, ProviderNotImplementedError
from ..settings import get_settings
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider


class LLMProvider(Protocol):
    name: str

    def chat(self, prompt: str) -> str: ...


class EchoProvider:
    name = "echo"

    def chat(self, prompt: str) -> str:
        return f"ECHO: {prompt}"


def get_provider() -> LLMProvider:
    provider = get_settings().llm_provider.strip().lower()
    if not provider:
        raise ProviderNotConfiguredError(
            "LLM_PROVIDER is not set. Use echo|gemini|openai|claude."
        )
    if provider == "echo":
        return EchoProvider()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "claude":
        return ClaudeProvider()
    raise ProviderNotImplementedError(
        f"Provider '{provider}' is not supported. Use echo|gemini|openai|claude."
    )

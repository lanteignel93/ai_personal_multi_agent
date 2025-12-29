from typing import Protocol

from ..errors import ProviderNotImplementedError
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
    provider = get_settings().llm_provider.lower()
    if provider == "echo":
        return EchoProvider()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "claude":
        return ClaudeProvider()
    raise ProviderNotImplementedError(f"Provider '{provider}' is not supported.")

from typing import Protocol

from ..settings import get_settings


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
    raise NotImplementedError(f"Provider '{provider}' is not implemented yet.")

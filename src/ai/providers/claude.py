from ..errors import ProviderNotConfiguredError, ProviderNotImplementedError
from ..settings import get_settings


class ClaudeProvider:
    name = "claude"

    def chat(self, prompt: str) -> str:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ProviderNotConfiguredError("ANTHROPIC_API_KEY is not set.")
        raise ProviderNotImplementedError("Claude provider is not implemented yet.")

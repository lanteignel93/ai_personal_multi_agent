from ..errors import ProviderNotConfiguredError, ProviderNotImplementedError
from ..settings import get_settings


class OpenAIProvider:
    name = "openai"

    def chat(self, prompt: str) -> str:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderNotConfiguredError("OPENAI_API_KEY is not set.")
        raise ProviderNotImplementedError("OpenAI provider is not implemented yet.")

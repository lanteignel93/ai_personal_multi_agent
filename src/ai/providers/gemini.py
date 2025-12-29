from ..errors import ProviderNotConfiguredError, ProviderNotImplementedError
from ..settings import get_settings


class GeminiProvider:
    name = "gemini"

    def chat(self, prompt: str) -> str:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ProviderNotConfiguredError("GEMINI_API_KEY is not set.")
        raise ProviderNotImplementedError("Gemini provider is not implemented yet.")

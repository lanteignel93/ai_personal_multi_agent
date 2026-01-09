import json
from typing import Protocol
from urllib import request

from ..errors import ProviderNotConfiguredError, ProviderNotImplementedError
from ..settings import get_settings


class EmbeddingProvider(Protocol):
    name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class GeminiEmbeddingProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("embedding text must be non-empty")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:embedContent?key={self._api_key}"
        )
        payload = {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]},
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return list(body["embedding"]["values"])


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    provider = settings.embedding_provider.strip().lower()
    if not provider:
        raise ProviderNotConfiguredError("EMBEDDING_PROVIDER is not set.")
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ProviderNotConfiguredError("GEMINI_API_KEY is not set.")
        return GeminiEmbeddingProvider(
            settings.gemini_api_key, settings.gemini_embedding_model
        )
    raise ProviderNotImplementedError(
        f"Embedding provider '{provider}' is not supported. Use gemini."
    )

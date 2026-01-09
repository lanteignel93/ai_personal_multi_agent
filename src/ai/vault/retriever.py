import json
import math
import sqlite3
from pathlib import Path

from ..providers.embeddings import EmbeddingProvider
from .models import VaultSearchResult


def query_vault_index(
    vault_name: str,
    index_path: Path,
    query: str,
    provider: EmbeddingProvider,
    *,
    top_k: int = 5,
) -> list[VaultSearchResult]:
    if not query.strip():
        raise ValueError("query must be non-empty")
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found: {index_path}")

    query_vec = provider.embed_texts([query])[0]
    results: list[VaultSearchResult] = []

    with sqlite3.connect(index_path) as conn:
        rows = conn.execute(
            "SELECT file_path, heading_path, text, embedding_json FROM chunks"
        ).fetchall()

    for file_path, heading_path, text, embedding_json in rows:
        vec = json.loads(embedding_json)
        score = _cosine_similarity(query_vec, vec)
        results.append(
            VaultSearchResult(
                vault=vault_name,
                score=score,
                text=text,
                file_path=file_path,
                heading_path=heading_path,
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if denom == 0.0:
        return 0.0
    return dot / denom

from pathlib import Path

from ai.vault.indexer import index_vault
from ai.vault.retriever import query_vault_index


class DummyEmbeddingProvider:
    name = "dummy"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            t = text.lower()
            vectors.append([float(t.count("alpha")), float(t.count("beta"))])
        return vectors


def test_index_and_query(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "a.md").write_text("alpha alpha alpha", encoding="utf-8")
    (vault_path / "b.md").write_text("beta beta", encoding="utf-8")

    index_path = tmp_path / "index.sqlite3"
    provider = DummyEmbeddingProvider()

    count = index_vault("personal", vault_path, index_path, provider)
    assert count > 0

    results = query_vault_index("personal", index_path, "alpha", provider, top_k=1)
    assert results[0].file_path.endswith("a.md")

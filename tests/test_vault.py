from pathlib import Path

from ai.cli import _clean_snippet, _filter_results
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

    count = index_vault(
        "personal",
        vault_path,
        index_path,
        provider,
        mode="rebuild",
        show_progress=False,
    )
    assert count > 0

    results = query_vault_index("personal", index_path, "alpha", provider, top_k=1)
    assert results[0].file_path.endswith("a.md")


def test_update_new_indexes_only_new_files(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "a.md").write_text("alpha alpha alpha", encoding="utf-8")
    (vault_path / "b.md").write_text("beta beta", encoding="utf-8")

    index_path = tmp_path / "index.sqlite3"
    provider = DummyEmbeddingProvider()

    index_vault(
        "personal",
        vault_path,
        index_path,
        provider,
        mode="rebuild",
        show_progress=False,
    )
    (vault_path / "c.md").write_text("alpha beta beta beta beta", encoding="utf-8")
    index_vault(
        "personal",
        vault_path,
        index_path,
        provider,
        mode="update-new",
        show_progress=False,
    )

    results = query_vault_index(
        "personal",
        index_path,
        "alpha beta beta beta beta",
        provider,
        top_k=1,
    )
    assert results[0].file_path.endswith("c.md")


def test_update_all_reindexes_changed_files(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "a.md").write_text("alpha alpha alpha", encoding="utf-8")
    (vault_path / "b.md").write_text("beta beta", encoding="utf-8")

    index_path = tmp_path / "index.sqlite3"
    provider = DummyEmbeddingProvider()

    index_vault(
        "personal",
        vault_path,
        index_path,
        provider,
        mode="rebuild",
        show_progress=False,
    )
    results = query_vault_index(
        "personal",
        index_path,
        "alpha beta beta beta beta",
        provider,
        top_k=1,
    )
    assert results[0].file_path.endswith("b.md")

    (vault_path / "a.md").write_text("alpha beta beta beta beta", encoding="utf-8")
    index_vault(
        "personal",
        vault_path,
        index_path,
        provider,
        mode="update-all",
        show_progress=False,
    )
    results = query_vault_index(
        "personal",
        index_path,
        "alpha beta beta beta beta",
        provider,
        top_k=1,
    )
    assert results[0].file_path.endswith("a.md")


def test_clean_snippet_strips_code_blocks() -> None:
    raw = "Hello\n```dataview\nTABLE X\n```\nWorld"
    cleaned = _clean_snippet(raw)
    assert "dataview" not in cleaned
    assert "Hello" in cleaned
    assert "World" in cleaned


def test_filter_results_excludes_templates() -> None:
    class DummyResult:
        def __init__(self, path: str) -> None:
            self.file_path = path

    results = [
        DummyResult("/vault/Templates/Note.md"),
        DummyResult("/vault/Notes/Real.md"),
    ]
    filtered = _filter_results(
        results,
        exclude_templates=True,
        path_contains=[],
        path_excludes=[],
    )
    assert len(filtered) == 1

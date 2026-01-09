import hashlib
import json
import sqlite3
from pathlib import Path

from tqdm import tqdm

from ..providers.embeddings import EmbeddingProvider
from .models import VaultChunk


def index_vault(
    vault_name: str,
    vault_path: Path,
    index_path: Path,
    provider: EmbeddingProvider,
    *,
    mode: str = "update-all",
    max_words: int = 800,
    overlap_words: int = 100,
    batch_size: int = 16,
    show_progress: bool = True,
    cleanup_deleted: bool = False,
) -> int:
    if not vault_name.strip():
        raise ValueError("vault_name must be non-empty")
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault path not found: {vault_path}")
    if mode not in {"rebuild", "update-all", "update-new"}:
        raise ValueError("mode must be rebuild, update-all, or update-new")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "rebuild" and index_path.exists():
        index_path.unlink()

    chunks: list[VaultChunk] = []

    with sqlite3.connect(index_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                file_path TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                mtime REAL NOT NULL,
                last_indexed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                heading_path TEXT NOT NULL,
                text TEXT NOT NULL,
                embedding_json TEXT NOT NULL
            )
            """
        )
        existing_hashes = {}
        if mode != "rebuild":
            existing_hashes = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT file_path, content_hash FROM files"
                ).fetchall()
            }
            if cleanup_deleted:
                live_paths = {str(p) for p in vault_path.rglob("*.md")}
                missing = set(existing_hashes.keys()) - live_paths
                for file_path in missing:
                    conn.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))
                    conn.execute("DELETE FROM files WHERE file_path = ?", (file_path,))
        for path in sorted(vault_path.rglob("*.md")):
            file_path = str(path)
            content_hash = _hash_file(path)
            mtime = path.stat().st_mtime
            if mode == "update-new" and file_path in existing_hashes:
                continue
            if mode == "update-all" and existing_hashes.get(file_path) == content_hash:
                continue
            if mode == "update-all" and file_path in existing_hashes:
                conn.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))
            chunks.extend(
                _collect_file_chunks(
                    path,
                    max_words=max_words,
                    overlap_words=overlap_words,
                )
            )
            conn.execute(
                """
                INSERT INTO files (file_path, content_hash, mtime, last_indexed_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(file_path) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    mtime = excluded.mtime,
                    last_indexed_at = CURRENT_TIMESTAMP
                """,
                (file_path, content_hash, mtime),
            )
        batches = _batched(chunks, batch_size)
        iterator = (
            tqdm(batches, desc="Embedding batches", unit="batch")
            if show_progress
            else batches
        )
        for batch in iterator:
            vectors = provider.embed_texts([chunk.text for chunk in batch])
            for chunk, vector in zip(batch, vectors, strict=True):
                conn.execute(
                    """
                    INSERT INTO chunks (file_path, heading_path, text, embedding_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        chunk.file_path,
                        chunk.heading_path,
                        chunk.text,
                        json.dumps(vector),
                    ),
                )
        conn.commit()
    return len(chunks)


def _collect_file_chunks(
    path: Path, *, max_words: int, overlap_words: int
) -> list[VaultChunk]:
    chunks: list[VaultChunk] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for heading_path, section_text in _split_sections(text):
        for chunk_text in _chunk_text(section_text, max_words, overlap_words):
            if chunk_text.strip():
                chunks.append(
                    VaultChunk(
                        text=chunk_text,
                        file_path=str(path),
                        heading_path=heading_path,
                    )
                )
    return chunks


def _split_sections(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    sections: list[tuple[str, str]] = []
    heading_stack: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            heading_path = " > ".join(heading_stack)
            sections.append((heading_path, "\n".join(buffer)))
            buffer.clear()

    for line in lines:
        if line.lstrip().startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            if level <= 0:
                continue
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            buffer.append(line)
        else:
            buffer.append(line)

    flush()
    return sections


def _chunk_text(text: str, max_words: int, overlap_words: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(max_words - overlap_words, 1)
    chunks: list[str] = []
    for i in range(0, len(words), step):
        chunk = words[i : i + max_words]
        chunks.append(" ".join(chunk))
    return chunks


def _batched(items: list[VaultChunk], batch_size: int) -> list[list[VaultChunk]]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

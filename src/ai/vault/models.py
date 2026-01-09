from dataclasses import dataclass


@dataclass(frozen=True)
class VaultChunk:
    text: str
    file_path: str
    heading_path: str


@dataclass(frozen=True)
class VaultSearchResult:
    vault: str
    score: float
    text: str
    file_path: str
    heading_path: str

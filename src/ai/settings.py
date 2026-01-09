from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_provider: str = "echo"
    ai_ledger_path: Path = Path(".ai/task_ledger.db")
    ai_log_level: str = "INFO"
    embedding_provider: str = "gemini"
    gemini_embedding_model: str = "text-embedding-004"
    personal_vault_path: Path | None = None
    project_vault_path: Path | None = None
    vector_index_root: Path | None = None
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


def get_settings() -> Settings:
    return Settings()

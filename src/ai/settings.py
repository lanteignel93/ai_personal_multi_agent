from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_provider: str = "echo"
    ai_ledger_path: Path = Path(".ai/task_ledger.db")


def get_settings() -> Settings:
    return Settings()

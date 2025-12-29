import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .settings import get_settings


@dataclass
class TaskLedger:
    path: Path

    @classmethod
    def from_env(cls) -> "TaskLedger":
        path = get_settings().ai_ledger_path
        return cls(Path(path)).init_db()

    def init_db(self) -> "TaskLedger":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_query TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_steps (
                    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    agent_name TEXT NOT NULL,
                    input TEXT NOT NULL,
                    output TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        return self

    def log_task(self, user_query: str) -> int:
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute(
                "INSERT INTO tasks (user_query) VALUES (?)",
                (user_query,),
            )
            return int(cur.lastrowid)

    def log_step(
        self,
        task_id: int,
        agent_name: str,
        input_text: str,
        output_text: str,
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO agent_steps (task_id, agent_name, input, output)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, agent_name, input_text, output_text),
            )

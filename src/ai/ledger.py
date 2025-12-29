import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .settings import get_settings


@dataclass
class TaskLedger:
    path: Path
    _task_statuses = {"started", "completed", "failed"}
    _step_statuses = {"completed", "failed"}

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
                    command TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    completed_at TEXT,
                    error TEXT,
                    metadata_json TEXT
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
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    error TEXT,
                    duration_ms INTEGER,
                    metadata_json TEXT
                )
                """
            )
            self._ensure_columns(
                conn,
                "tasks",
                {
                    "command": "TEXT NOT NULL DEFAULT ''",
                    "completed_at": "TEXT",
                    "error": "TEXT",
                    "metadata_json": "TEXT",
                },
            )
            self._ensure_columns(
                conn,
                "agent_steps",
                {
                    "status": "TEXT DEFAULT 'completed'",
                    "error": "TEXT",
                    "duration_ms": "INTEGER",
                    "metadata_json": "TEXT",
                },
            )
        return self

    def log_task(self, user_query: str, command: str) -> int:
        if not user_query.strip():
            raise ValueError("user_query must be non-empty")
        if not command.strip():
            raise ValueError("command must be non-empty")
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (user_query, command, status)
                VALUES (?, ?, ?)
                """,
                (user_query, command, "started"),
            )
            return int(cur.lastrowid)

    def log_step(
        self,
        task_id: int,
        agent_name: str,
        input_text: str,
        output_text: str,
        status: str = "completed",
        error: str | None = None,
        duration_ms: int | None = None,
        metadata_json: str | None = None,
    ) -> None:
        if task_id <= 0:
            raise ValueError("task_id must be positive")
        if not agent_name.strip():
            raise ValueError("agent_name must be non-empty")
        if not input_text.strip():
            raise ValueError("input_text must be non-empty")
        if not output_text.strip():
            raise ValueError("output_text must be non-empty")
        if status not in self._step_statuses:
            raise ValueError("status must be 'completed' or 'failed'")
        if duration_ms is not None and duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO agent_steps (
                    task_id, agent_name, input, output, 
                    status, error, duration_ms, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    agent_name,
                    input_text,
                    output_text,
                    status,
                    error,
                    duration_ms,
                    metadata_json,
                ),
            )

    def complete_task(
        self, task_id: int, status: str, error: str | None = None
    ) -> None:
        if task_id <= 0:
            raise ValueError("task_id must be positive")
        if status not in self._task_statuses:
            raise ValueError("status must be 'started', 'completed', or 'failed'")
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, completed_at = CURRENT_TIMESTAMP, error = ?
                WHERE task_id = ?
                """,
                (status, error, task_id),
            )

    @staticmethod
    def _ensure_columns(
        conn: sqlite3.Connection, table: str, columns: dict[str, str]
    ) -> None:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

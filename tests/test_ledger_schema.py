import sqlite3

from ai.ledger import TaskLedger


def test_ledger_schema_has_new_columns(tmp_path) -> None:
    ledger = TaskLedger(tmp_path / "ledger.db").init_db()
    with sqlite3.connect(ledger.path) as conn:
        task_cols = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
        step_cols = {row[1] for row in conn.execute("PRAGMA table_info(agent_steps)")}

    assert "command" in task_cols
    assert "completed_at" in task_cols
    assert "error" in task_cols
    assert "metadata_json" in task_cols
    assert "status" in step_cols
    assert "duration_ms" in step_cols

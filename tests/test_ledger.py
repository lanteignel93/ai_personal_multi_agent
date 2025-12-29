import sqlite3

from ai.ledger import TaskLedger


def test_ledger_writes(tmp_path) -> None:
    ledger = TaskLedger(tmp_path / "ledger.db").init_db()
    task_id = ledger.log_task("hello")
    ledger.log_step(task_id, "echo", "hello", "ECHO: hello")

    with sqlite3.connect(ledger.path) as conn:
        tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        steps = conn.execute("SELECT COUNT(*) FROM agent_steps").fetchone()[0]

    assert tasks == 1
    assert steps == 1

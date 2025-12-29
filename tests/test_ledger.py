import sqlite3

import pytest

from ai.ledger import TaskLedger


def test_ledger_writes(tmp_path) -> None:
    ledger = TaskLedger(tmp_path / "ledger.db").init_db()
    task_id = ledger.log_task("hello", command="chat")
    ledger.log_step(task_id, "echo", "hello", "ECHO: hello")
    ledger.complete_task(task_id, status="completed")

    with sqlite3.connect(ledger.path) as conn:
        tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        steps = conn.execute("SELECT COUNT(*) FROM agent_steps").fetchone()[0]

    assert tasks == 1
    assert steps == 1


def test_ledger_rejects_empty_task_fields(tmp_path) -> None:
    ledger = TaskLedger(tmp_path / "ledger.db").init_db()
    with pytest.raises(ValueError):
        ledger.log_task("   ", command="chat")
    with pytest.raises(ValueError):
        ledger.log_task("hello", command="   ")


def test_ledger_rejects_invalid_step_fields(tmp_path) -> None:
    ledger = TaskLedger(tmp_path / "ledger.db").init_db()
    task_id = ledger.log_task("hello", command="chat")
    with pytest.raises(ValueError):
        ledger.log_step(0, "echo", "hi", "ok")
    with pytest.raises(ValueError):
        ledger.log_step(task_id, "   ", "hi", "ok")
    with pytest.raises(ValueError):
        ledger.log_step(task_id, "echo", "   ", "ok")
    with pytest.raises(ValueError):
        ledger.log_step(task_id, "echo", "hi", "   ")
    with pytest.raises(ValueError):
        ledger.log_step(task_id, "echo", "hi", "ok", status="unknown")
    with pytest.raises(ValueError):
        ledger.log_step(task_id, "echo", "hi", "ok", duration_ms=-1)

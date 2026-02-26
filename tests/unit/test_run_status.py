"""Unit tests for run_status."""
from pathlib import Path

import pytest

from plugins.cursor_cli import cli


def test_status_no_pid_file(sessions_dir):
    out = cli.run_status("nonexistent-uid", sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["agent_uid"] == "nonexistent-uid"
    assert out["run_status"] == "failed"
    assert "No PID file" in out["message"]


def test_status_invalid_pid_file(sessions_dir):
    pid_path = Path(sessions_dir) / "some-uid.pid"
    pid_path.write_text("not-a-number")
    out = cli.run_status("some-uid", sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["run_status"] == "failed"
    assert "Invalid" in out["message"]


def test_status_process_gone_exitcode_zero(sessions_dir):
    uid = "done-uid"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{uid}.pid").write_text("999999")  # PID that does not exist
    (base / f"{uid}.exitcode").write_text("0")
    out = cli.run_status(uid, sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["run_status"] == "completed"
    assert out.get("exit_code") == 0


def test_status_process_gone_exitcode_nonzero(sessions_dir):
    uid = "failed-uid"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{uid}.pid").write_text("999998")
    (base / f"{uid}.exitcode").write_text("1")
    out = cli.run_status(uid, sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["run_status"] == "failed"
    assert out.get("exit_code") == 1


def test_status_process_running(sessions_dir):
    import os
    uid = "running-uid"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{uid}.pid").write_text(str(os.getpid()))  # current process
    out = cli.run_status(uid, sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["run_status"] == "running"


def test_status_process_gone_no_exitcode(sessions_dir):
    uid = "unknown-uid"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{uid}.pid").write_text("999997")
    out = cli.run_status(uid, sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["run_status"] == "completed"
    assert "exit code unknown" in out.get("message", "").lower()


def test_status_exitcode_file_invalid_content(sessions_dir):
    """Exit code file exists but content is not an int; fall through to 'exit code unknown'."""
    uid = "bad-exitcode-uid"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{uid}.pid").write_text("999996")
    (base / f"{uid}.exitcode").write_text("not-a-number")
    out = cli.run_status(uid, sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["run_status"] == "completed"
    assert "exit code unknown" in out.get("message", "").lower()

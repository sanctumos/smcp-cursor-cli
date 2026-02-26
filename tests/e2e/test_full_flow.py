"""End-to-end tests: full start -> status -> output flow with fake agent."""
import json
import time
from pathlib import Path

import pytest

from plugins.cursor_cli import cli


def test_full_flow_start_status_output(sessions_dir, fake_agent_script):
    # Start
    out_start = cli.run_start(
        "e2e test prompt",
        sessions_dir=sessions_dir,
        cmd=fake_agent_script,
    )
    assert out_start["status"] == "success"
    uid = out_start["agent_uid"]
    base = Path(sessions_dir)

    assert (base / f"{uid}.pid").exists()
    assert (base / f"{uid}.txt").exists()

    # Status: eventually completed (fake agent exits quickly)
    for _ in range(50):
        out_status = cli.run_status(uid, sessions_dir=sessions_dir)
        assert out_status["status"] == "success"
        assert out_status["agent_uid"] == uid
        if out_status["run_status"] == "running":
            time.sleep(0.1)
            continue
        assert out_status["run_status"] in ("completed", "failed")
        break
    else:
        pytest.fail("Run did not complete within 5s")

    # Output
    out_output = cli.run_output(uid, sessions_dir=sessions_dir)
    assert out_output["status"] == "success"
    assert "fake agent output" in out_output["output"]


def test_output_available_while_running(sessions_dir, tmp_path):
    """Output file can be read while process is still running (partial output)."""
    slow_script = tmp_path / "slow_agent"
    slow_script.write_text(
        "#!/bin/sh\n"
        "echo 'first line'\n"
        "sleep 2\n"
        "echo 'second line'\n"
        "exit 0\n"
    )
    slow_script.chmod(0o755)

    out_start = cli.run_start("x", sessions_dir=sessions_dir, cmd=str(slow_script))
    assert out_start["status"] == "success"
    uid = out_start["agent_uid"]

    time.sleep(0.5)
    out_output = cli.run_output(uid, sessions_dir=sessions_dir)
    assert out_output["status"] == "success"
    assert "first line" in out_output["output"]
    # May or may not have second line yet
    assert "first line" in out_output["output"]

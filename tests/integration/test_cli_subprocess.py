"""Integration tests: run the CLI as a subprocess."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLI_MODULE = "plugins.cursor_cli"


def run_cli(*args):
    """Run the plugin CLI from repo root; return (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", CLI_MODULE] + list(args)
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=10)
    return result.returncode, result.stdout, result.stderr


def test_cli_describe():
    code, out, err = run_cli("--describe")
    assert code == 0
    data = json.loads(out)
    assert data["plugin"]["name"] == "cursor_cli"
    assert len(data["commands"]) == 3


def test_cli_no_args_prints_help():
    code, out, err = run_cli()
    assert code != 0
    assert "usage" in out.lower() or "Usage" in out


def test_cli_start_with_nonexistent_cmd(sessions_dir):
    code, out, err = run_cli(
        "start",
        "--prompt", "x",
        "--sessions-dir", sessions_dir,
        "--cmd", "/nonexistent/fake/agent",
    )
    assert code == 1
    data = json.loads(out)
    assert data["status"] == "error"
    assert "agent_uid" in data


def test_cli_start_and_status_and_output(sessions_dir, fake_agent_script):
    code, out, err = run_cli(
        "start",
        "--prompt", "hi",
        "--sessions-dir", sessions_dir,
        "--cmd", fake_agent_script,
    )
    assert code == 0
    data = json.loads(out)
    assert data["status"] == "success"
    uid = data["agent_uid"]

    # Poll status until completed (fake agent exits immediately)
    for _ in range(20):
        code2, out2, _ = run_cli("status", "--agent-uid", uid, "--sessions-dir", sessions_dir)
        assert code2 == 0
        data2 = json.loads(out2)
        if data2.get("run_status") in ("completed", "failed"):
            break
        __import__("time").sleep(0.1)
    else:
        pytest.fail("status did not become completed")

    code3, out3, _ = run_cli("output", "--agent-uid", uid, "--sessions-dir", sessions_dir)
    assert code3 == 0
    data3 = json.loads(out3)
    assert data3["status"] == "success"
    assert "fake agent output" in data3["output"]


def test_cli_status_no_pid(sessions_dir):
    code, out, err = run_cli("status", "--agent-uid", "nonexistent", "--sessions-dir", sessions_dir)
    assert code == 0
    data = json.loads(out)
    assert data["run_status"] == "failed"


def test_cli_output_no_file(sessions_dir):
    code, out, err = run_cli("output", "--agent-uid", "no-file", "--sessions-dir", sessions_dir)
    assert code == 1
    data = json.loads(out)
    assert data["status"] == "error"

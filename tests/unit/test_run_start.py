"""Unit tests for run_start (with mocked subprocess)."""
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from plugins.cursor_cli import cli


def test_start_returns_agent_uid_and_creates_files(sessions_dir, fake_agent_script):
    out = cli.run_start("test prompt", sessions_dir=sessions_dir, cmd=fake_agent_script)
    assert out["status"] == "success"
    agent_uid = out["agent_uid"]
    assert len(agent_uid) == 32 and agent_uid.isalnum()
    assert out["sessions_dir"] == sessions_dir

    base = __import__("pathlib").Path(sessions_dir)
    assert (base / f"{agent_uid}.pid").exists()
    assert (base / f"{agent_uid}.txt").exists()


def test_start_cmd_not_found(sessions_dir):
    out = cli.run_start("test", sessions_dir=sessions_dir, cmd="/nonexistent/binary/agent")
    assert out["status"] == "error"
    assert "not found" in out["error"].lower() or "No such file" in out["error"]
    assert "agent_uid" in out


@patch("plugins.cursor_cli.cli.subprocess.Popen")
def test_start_popen_called_with_argv(mock_popen, sessions_dir, fake_agent_script):
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    mock_popen.return_value = mock_proc

    out = cli.run_start("hello world", sessions_dir=sessions_dir, cmd=fake_agent_script)
    assert out["status"] == "success"
    mock_popen.assert_called_once()
    call_args = mock_popen.call_args[0][0]
    assert call_args[0] == fake_agent_script
    assert "-p" in call_args
    assert "hello world" in call_args
    assert "--output-format" in call_args
    assert "text" in call_args
    assert "--trust" in call_args


@patch("plugins.cursor_cli.cli.subprocess.Popen")
def test_start_uses_workspace_as_cwd(mock_popen, sessions_dir, fake_agent_script, tmp_path):
    workspace = str(tmp_path / "workspace")
    tmp_path.joinpath("workspace").mkdir()
    mock_proc = MagicMock()
    mock_proc.pid = 11111
    mock_popen.return_value = mock_proc

    cli.run_start("x", sessions_dir=sessions_dir, cmd=fake_agent_script, workspace=workspace)
    mock_popen.assert_called_once()
    assert mock_popen.call_args[1]["cwd"] == workspace

"""Unit tests for run_start exception paths."""
from unittest.mock import MagicMock, patch

import pytest

from plugins.cursor_cli import cli


@patch("plugins.cursor_cli.cli.subprocess.Popen")
def test_start_popen_raises_exception(mock_popen, sessions_dir, fake_agent_script):
    mock_popen.side_effect = RuntimeError("subprocess failed")
    out = cli.run_start("x", sessions_dir=sessions_dir, cmd=fake_agent_script)
    assert out["status"] == "error"
    assert "subprocess failed" in out["error"]
    assert "agent_uid" in out

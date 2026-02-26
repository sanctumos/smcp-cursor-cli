"""Unit tests for main() entry point."""
import json
from io import StringIO
from unittest.mock import patch

import pytest

from plugins.cursor_cli import cli


def test_main_describe(capsys):
    with patch("sys.argv", ["cli", "--describe"]):
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0
    out, _ = capsys.readouterr()
    data = json.loads(out)
    assert data["plugin"]["name"] == "cursor_cli"


def test_main_no_command_prints_help(capsys):
    with patch("sys.argv", ["cli"]):
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code != 0
    out, _ = capsys.readouterr()
    assert "usage" in out.lower() or "Usage" in out


def test_main_invalid_command_exits_with_argparse_error(capsys):
    """Invalid subcommand causes argparse to exit with 2 before main's else branch."""
    with patch("sys.argv", ["cli", "unknowncmd"]):
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 2


def test_main_start_success(capsys, sessions_dir, fake_agent_script):
    with patch("sys.argv", [
        "cli", "start",
        "--prompt", "hi",
        "--sessions-dir", sessions_dir,
        "--cmd", fake_agent_script,
    ]):
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0
    out, _ = capsys.readouterr()
    data = json.loads(out)
    assert data["status"] == "success"
    assert "agent_uid" in data


def test_main_status_and_output(capsys, sessions_dir):
    from pathlib import Path
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    uid = "test-uid-123"
    (base / f"{uid}.pid").write_text("99999")
    (base / f"{uid}.exitcode").write_text("0")
    (base / f"{uid}.txt").write_text("output content")

    with patch("sys.argv", ["cli", "status", "--agent-uid", uid, "--sessions-dir", sessions_dir]):
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0
    out, _ = capsys.readouterr()
    data = json.loads(out)
    assert data["run_status"] in ("completed", "failed")

    with patch("sys.argv", ["cli", "output", "--agent-uid", uid, "--sessions-dir", sessions_dir]):
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0
    out2, _ = capsys.readouterr()
    data2 = json.loads(out2)
    assert data2["status"] == "success"
    assert data2["output"] == "output content"

"""Unit tests for run_output."""
from pathlib import Path
from unittest.mock import patch

import pytest

from plugins.cursor_cli import cli


def test_output_no_file(sessions_dir):
    out = cli.run_output("no-such-uid", sessions_dir=sessions_dir)
    assert out["status"] == "error"
    assert "No output file" in out["error"]
    assert out["agent_uid"] == "no-such-uid"


def test_output_success(sessions_dir):
    uid = "abc123"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    content = "line one\nline two\n"
    (base / f"{uid}.txt").write_text(content)
    out = cli.run_output(uid, sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["agent_uid"] == uid
    assert out["output"] == content


def test_output_unicode(sessions_dir):
    uid = "unicode-uid"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    content = "café \n 日本語\n"
    (base / f"{uid}.txt").write_text(content, encoding="utf-8")
    out = cli.run_output(uid, sessions_dir=sessions_dir)
    assert out["status"] == "success"
    assert out["output"] == content


def test_output_read_raises_oserror(sessions_dir):
    """When read_text raises OSError, return error dict."""
    uid = "oserror-uid"
    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{uid}.txt").write_text("x")
    with patch("plugins.cursor_cli.cli.Path.read_text", side_effect=OSError(13, "Permission denied")):
        out = cli.run_output(uid, sessions_dir=sessions_dir)
    assert out["status"] == "error"
    assert "error" in out
    assert out["agent_uid"] == uid

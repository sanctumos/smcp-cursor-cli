"""Unit tests for _resolve_sessions_dir, _resolve_cmd, _resolve_workspace."""
import os

import pytest

from plugins.cursor_cli import cli


def test_resolve_sessions_dir_arg_overrides(sessions_dir):
    assert cli._resolve_sessions_dir(sessions_dir) == sessions_dir


def test_resolve_sessions_dir_default(monkeypatch):
    monkeypatch.delenv("CURSOR_CLI_SESSIONS_DIR", raising=False)
    default = cli._resolve_sessions_dir(None)
    assert default
    assert ".cursor" in default or "cursor" in default
    assert cli._resolve_sessions_dir("") == default


def test_resolve_sessions_dir_env(monkeypatch, sessions_dir):
    monkeypatch.setenv("CURSOR_CLI_SESSIONS_DIR", sessions_dir)
    assert cli._resolve_sessions_dir(None) == sessions_dir


def test_resolve_cmd_arg_overrides():
    assert cli._resolve_cmd("cursor-agent") == "cursor-agent"


def test_resolve_cmd_default(monkeypatch):
    monkeypatch.delenv("CURSOR_CLI_CMD", raising=False)
    assert cli._resolve_cmd(None) == "agent"
    assert cli._resolve_cmd("") == "agent"


def test_resolve_cmd_env(monkeypatch):
    monkeypatch.setenv("CURSOR_CLI_CMD", "my-agent")
    assert cli._resolve_cmd(None) == "my-agent"


def test_resolve_workspace_arg_overrides():
    assert cli._resolve_workspace("/tmp/ws") == "/tmp/ws"


def test_resolve_workspace_empty_uses_default(monkeypatch):
    monkeypatch.delenv("CURSOR_CLI_WORKSPACE", raising=False)
    assert cli._resolve_workspace(None) is None or cli._resolve_workspace("") == ""


def test_resolve_workspace_env(monkeypatch):
    monkeypatch.setenv("CURSOR_CLI_WORKSPACE", "/env/ws")
    assert cli._resolve_workspace(None) == "/env/ws"

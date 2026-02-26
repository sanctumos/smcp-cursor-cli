"""Unit tests for get_plugin_description and describe output."""
import json

import pytest

from plugins.cursor_cli import cli


def test_get_plugin_description_structure():
    desc = cli.get_plugin_description()
    assert "plugin" in desc
    assert "commands" in desc
    assert desc["plugin"]["name"] == "cursor_cli"
    assert desc["plugin"]["version"] == "0.1.0"
    assert isinstance(desc["commands"], list)
    assert len(desc["commands"]) == 3


def test_get_plugin_description_commands():
    desc = cli.get_plugin_description()
    names = {c["name"] for c in desc["commands"]}
    assert names == {"start", "status", "output"}


def test_get_plugin_description_start_params():
    desc = cli.get_plugin_description()
    start = next(c for c in desc["commands"] if c["name"] == "start")
    param_names = {p["name"] for p in start["parameters"]}
    assert "prompt" in param_names
    assert start["parameters"][0]["required"] is True
    assert "workspace" in param_names
    assert "cmd" in param_names
    assert "sessions_dir" in param_names


def test_get_plugin_description_status_output_params():
    desc = cli.get_plugin_description()
    for cmd_name in ("status", "output"):
        cmd = next(c for c in desc["commands"] if c["name"] == cmd_name)
        param_names = {p["name"] for p in cmd["parameters"]}
        assert "agent_uid" in param_names
        assert "sessions_dir" in param_names


def test_describe_json_serializable():
    desc = cli.get_plugin_description()
    s = json.dumps(desc)
    loaded = json.loads(s)
    assert loaded == desc

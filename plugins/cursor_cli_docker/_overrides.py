# smcp-cursor-cli-docker — default configuration
# Copyright (c) 2025 SanctumOS
# SPDX-License-Identifier: AGPL-3.0
# See LICENSE and LICENSE-DOCS for full terms.

"""
Resolve defaults for the Docker-sandboxed Cursor CLI plugin.

Priority (highest to lowest):
  1. Tool argument (passed at call time)
  2. Environment variable
  3. Auto-detected / hardcoded default
"""

import os
from pathlib import Path


def get_default_image() -> str:
    return os.environ.get("CURSOR_DOCKER_IMAGE", "smcp-cursor-sandbox")


def get_default_cmd() -> str:
    return os.environ.get("CURSOR_CLI_CMD", "agent")


def get_default_model() -> str:
    """Model for Cursor CLI. Default composer-2 (avoids deprecated `auto` / surprise premium use)."""
    return os.environ.get("CURSOR_CLI_MODEL", "composer-2")


def get_default_workspace():
    return os.environ.get("CURSOR_CLI_WORKSPACE", None)


def get_default_sessions_dir() -> str:
    return os.environ.get(
        "CURSOR_CLI_SESSIONS_DIR",
        os.path.expanduser("~/.cursor/smcp-docker-sessions"),
    )


def get_default_cursor_host_bin() -> str:
    """Resolve the host path to the cursor CLI binary for mounting."""
    env = os.environ.get("CURSOR_CLI_HOST_PATH")
    if env:
        return env
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".local", "bin", "agent"),
        "/usr/local/bin/agent",
        "/usr/bin/agent",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
        p = Path(c)
        if p.is_symlink():
            resolved = str(p.resolve())
            if os.path.isfile(resolved):
                return c
    return os.path.join(home, ".local", "bin", "agent")


def get_default_cursor_agent_dir():
    """Resolve the host path to the cursor-agent data directory."""
    env = os.environ.get("CURSOR_AGENT_HOST_DIR")
    if env:
        return env
    home = os.path.expanduser("~")
    d = os.path.join(home, ".local", "share", "cursor-agent")
    if os.path.isdir(d):
        return d
    return None


def get_default_cursor_config_dir() -> str:
    """Resolve the host path to ~/.cursor for auth config."""
    env = os.environ.get("CURSOR_CONFIG_HOST_DIR")
    if env:
        return env
    return os.path.expanduser("~/.cursor")


def get_default_cursor_xdg_config_dir() -> str:
    """Resolve ~/.config/cursor which holds auth.json (tokens)."""
    env = os.environ.get("CURSOR_XDG_CONFIG_DIR")
    if env:
        return env
    return os.path.expanduser("~/.config/cursor")


def get_extra_host_mounts():
    """
    Return a list of (host_path, container_path, mode) tuples for additional
    bind mounts.  Set via CURSOR_DOCKER_EXTRA_MOUNTS as a comma-separated
    list of host:container or host:container:mode entries.
    """
    raw = os.environ.get("CURSOR_DOCKER_EXTRA_MOUNTS", "")
    mounts = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) == 2:
            mounts.append((parts[0], parts[1], "rw"))
        elif len(parts) >= 3:
            mounts.append((parts[0], parts[1], parts[2]))
    return mounts


def get_dockerfile_dir() -> str:
    """Return the directory containing the Dockerfile for this plugin."""
    return os.path.dirname(os.path.abspath(__file__))

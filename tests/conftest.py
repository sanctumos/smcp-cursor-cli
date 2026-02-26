"""Shared fixtures and path setup for smcp-cursor-cli tests."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Allow importing the plugin module when running from repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def sessions_dir(tmp_path):
    """Temporary directory for session files (PID, output, exitcode)."""
    d = tmp_path / "sessions"
    d.mkdir()
    return str(d)


@pytest.fixture
def fake_agent_script(tmp_path):
    """Path to a script that acts like a minimal agent: writes to stdout and exits with 0."""
    script = tmp_path / "fake_agent"
    script.write_text(
        "#!/bin/sh\n"
        "echo 'fake agent output'\n"
        "exit 0\n"
    )
    script.chmod(0o755)
    return str(script)

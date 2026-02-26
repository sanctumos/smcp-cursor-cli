# smcp-cursor-cli — constant overrides (optional)
# Copyright (c) 2025 SanctumOS
# SPDX-License-Identifier: AGPL-3.0
# See LICENSE and LICENSE-DOCS for full terms.

"""
Optional hardcoded overrides for CLI command, workspace, session dir, or API keys.
Not recommended: prefer environment variables or tool arguments.
If you uncomment and set values below, they are used when no argument or env var is provided.
"""

# -----------------------------------------------------------------------------
# CONSTANT OVERRIDES (commented out — uncomment to hardcode)
# -----------------------------------------------------------------------------
# CURSOR_CLI_CMD = "agent"                    # or "cursor-agent"
# CURSOR_CLI_WORKSPACE = "/path/to/workspace"
# CURSOR_CLI_SESSIONS_DIR = os.path.expanduser("~/.cursor/smcp-sessions")
# CURSOR_API_KEY = ""                         # if ever required
# -----------------------------------------------------------------------------

import os

# Defaults: env vars (or uncommented constants above) when no tool argument is set.
def get_default_cmd():
    return os.environ.get("CURSOR_CLI_CMD", "agent")

def get_default_workspace():
    return os.environ.get("CURSOR_CLI_WORKSPACE", None)

def get_default_sessions_dir():
    return os.environ.get("CURSOR_CLI_SESSIONS_DIR", os.path.expanduser("~/.cursor/smcp-sessions"))

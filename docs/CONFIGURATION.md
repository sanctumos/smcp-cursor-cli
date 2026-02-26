# Configuration

All configurable values can be supplied either as **tool arguments** (from the agent) or as **environment variables**. When both are present, **the tool argument overrides the environment variable.** This works with Sanctum’s MCP environment system: set defaults via env, override per call via arguments.

---

## Environment variables

| Variable | Default | Used by | Description |
|----------|---------|--------|-------------|
| `CURSOR_CLI_CMD` | `agent` | start | Cursor CLI command (e.g. `agent` or `cursor-agent`). |
| `CURSOR_CLI_WORKSPACE` | (none) | start | Working directory for the agent run. |
| `CURSOR_CLI_SESSIONS_DIR` | `~/.cursor/smcp-sessions` | start, status, output | Directory for session files (`.txt`, `.pid`, `.exitcode`). |

These are read by the plugin when the corresponding tool argument is not provided.

---

## Tool arguments

Each tool can accept arguments that override the environment (see [Tools reference](TOOLS_REFERENCE.md) for full lists).

- **cursor_cli__start**: `prompt` (required), `workspace`, `cmd`, `sessions_dir`
- **cursor_cli__status**: `agent_uid` (required), `sessions_dir`
- **cursor_cli__output**: `agent_uid` (required), `sessions_dir`

Precedence: **argument > environment variable > default.**

---

## Optional hardcoded overrides

For local or one-off setups, you can hardcode values in the plugin (not recommended for shared or production use).

Edit **plugins/cursor_cli/_overrides.py**. At the top there is a commented block:

```python
# -----------------------------------------------------------------------------
# CONSTANT OVERRIDES (commented out — uncomment to hardcode)
# -----------------------------------------------------------------------------
# CURSOR_CLI_CMD = "agent"                    # or "cursor-agent"
# CURSOR_CLI_WORKSPACE = "/path/to/workspace"
# CURSOR_CLI_SESSIONS_DIR = os.path.expanduser("~/.cursor/smcp-sessions")
# CURSOR_API_KEY = ""                         # if ever required
# -----------------------------------------------------------------------------
```

Uncomment and set the variables you need. These are used when no tool argument and no environment variable is set. The plugin’s `get_default_*` helpers in `_overrides.py` currently read only from the environment; if you uncomment the constants, you would typically also wire them into those helpers (or use env for defaults and overrides only for local overrides).

---

## Session directory layout

When `sessions_dir` is set (via argument or env), the plugin uses it for all session files. Default: `~/.cursor/smcp-sessions`.

For each run (each `agent_uid`), the plugin creates:

| File | Description |
|------|-------------|
| `<agent_uid>.txt` | Stdout and stderr of the Cursor CLI run. |
| `<agent_uid>.pid` | Process ID of the wrapper process. |
| `<agent_uid>.exitcode` | Exit code written when the run finishes (0 = completed, non-zero = failed). |

`cursor_cli__status` uses `.pid` and `.exitcode`; `cursor_cli__output` reads `.txt`.

---

## Multiple agents and sessions_dir

Multiple Cursor CLI agents can run at once; each has a unique `agent_uid`. All of them use the same `sessions_dir` (default or configured). Polling is always by `agent_uid`, so status and output are isolated per run.

If you run multiple SMCP instances or multiple users, use different `sessions_dir` per instance or user (e.g. via `CURSOR_CLI_SESSIONS_DIR` or the `sessions_dir` argument) to avoid mixing session files.

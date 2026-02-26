# cursor_cli — SMCP plugin

Runs Cursor CLI in non-interactive mode. Start an agent run, poll status, retrieve output. For use with Sanctum Tasks heartbeat.

## Commands

- **start** — Start `agent -p "<prompt>" --output-format text --trust` in the background. Returns `agent_uid`.
- **status** — Check run status: `running` | `completed` | `failed`. Requires `agent_uid`.
- **output** — Read the output file for an `agent_uid` (works while running or after completion).

## Configuration

- **Argument or env**: `prompt`, `workspace`, `cmd`, `sessions_dir`, `agent_uid` (for status/output). Tool argument overrides environment variable.
- **Env vars**: `CURSOR_CLI_CMD` (default `agent`), `CURSOR_CLI_WORKSPACE`, `CURSOR_CLI_SESSIONS_DIR`.
- **Optional overrides**: Edit `_overrides.py` to hardcode values (not recommended).

## Session files

Under `sessions_dir` (default `~/.cursor/smcp-sessions/`):

- `<agent_uid>.txt` — stdout/stderr of the agent run
- `<agent_uid>.pid` — PID of the wrapper process
- `<agent_uid>.exitcode` — exit code written when the run finishes

## Usage (SMCP)

When this plugin is in your SMCP `plugins/` directory, tools appear as:

- `cursor_cli__start`
- `cursor_cli__status`
- `cursor_cli__output`

Use with Sanctum Tasks heartbeat: create a task that polls `cursor_cli__status` until `completed` or `failed`, then calls `cursor_cli__output`.

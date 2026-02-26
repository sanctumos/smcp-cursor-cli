# Tools reference

When the plugin is loaded by SMCP, it exposes three MCP tools. Their names use the SMCP convention: **plugin name + double underscore + command** → `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output`.

---

## cursor_cli__start

Starts a Cursor CLI agent run in the background with the given prompt. Returns an **agent_uid** that you use for status and output.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `prompt` | string | Yes | Task prompt for the agent (e.g. "Refactor the auth module to use JWT"). |
| `workspace` | string | No | Working directory for the run. Overrides `CURSOR_CLI_WORKSPACE` if set. |
| `cmd` | string | No | Cursor CLI command (e.g. `agent` or `cursor-agent`). Overrides `CURSOR_CLI_CMD`. |
| `sessions_dir` | string | No | Directory for session files. Overrides `CURSOR_CLI_SESSIONS_DIR`. |

### Behavior

- Runs: `agent -p "<prompt>" --output-format text --trust` (or your `cmd`) in the background.
- Creates `<agent_uid>.txt` (output), `<agent_uid>.pid` (process id), and on exit `<agent_uid>.exitcode`.
- Returns immediately with `agent_uid`; the run continues in the background.

### Example result (success)

```json
{
  "status": "success",
  "agent_uid": "a1b2c3d4e5f6...",
  "message": "Agent started; use status and output with this agent_uid.",
  "sessions_dir": "/home/user/.cursor/smcp-sessions"
}
```

### Example result (error)

```json
{
  "status": "error",
  "error": "Cursor CLI command not found: agent",
  "agent_uid": "..."
}
```

---

## cursor_cli__status

Returns the run status for a given **agent_uid**: `running`, `completed`, or `failed`.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_uid` | string | Yes | Value returned from `cursor_cli__start`. |
| `sessions_dir` | string | No | Session directory if different from default. |

### Behavior

- Reads `<agent_uid>.pid` and, if present, `<agent_uid>.exitcode`.
- If the process is still running → `run_status: "running"`.
- If the process has exited and exitcode is 0 → `run_status: "completed"`.
- If the process has exited and exitcode is non-zero → `run_status: "failed"`.
- If there is no PID file or the run never started → `run_status: "failed"` with a message.

### Example result (running)

```json
{
  "status": "success",
  "agent_uid": "a1b2c3d4e5f6...",
  "run_status": "running",
  "message": "Agent is still running."
}
```

### Example result (completed)

```json
{
  "status": "success",
  "agent_uid": "a1b2c3d4e5f6...",
  "run_status": "completed",
  "exit_code": 0
}
```

### Example result (failed)

```json
{
  "status": "success",
  "agent_uid": "a1b2c3d4e5f6...",
  "run_status": "failed",
  "exit_code": 1
}
```

---

## cursor_cli__output

Returns the contents of the output file for a given **agent_uid**. You can call this while the run is still **running** (partial output) or after it has **completed**.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_uid` | string | Yes | Value returned from `cursor_cli__start`. |
| `sessions_dir` | string | No | Session directory if different from default. |

### Behavior

- Reads `<agent_uid>.txt` and returns its contents in the `output` field.
- If the file does not exist (e.g. invalid `agent_uid` or run never started), returns an error result.

### Example result (success)

```json
{
  "status": "success",
  "agent_uid": "a1b2c3d4e5f6...",
  "output": "Full stdout/stderr of the Cursor CLI run..."
}
```

### Example result (error)

```json
{
  "status": "error",
  "error": "No output file for agent_uid a1b2c3d4e5f6...",
  "agent_uid": "a1b2c3d4e5f6..."
}
```

---

## Typical flow

1. **tools/call** `cursor_cli__start` with `{"prompt": "Your task here"}` → get `agent_uid`.
2. **Poll** **tools/call** `cursor_cli__status` with `{"agent_uid": "<agent_uid>"}` until `run_status` is `completed` or `failed`.
3. **tools/call** `cursor_cli__output` with `{"agent_uid": "<agent_uid>"}` → get the run output and use it in your agent (e.g. memory or next step).

For the recommended pattern using a heartbeat queue, see [Sanctum Tasks integration](SANCTUM_TASKS.md).

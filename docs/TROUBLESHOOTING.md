# Troubleshooting

Common issues and how to fix them.

---

## Plugin not discovered by SMCP

**Symptom:** `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output` do not appear in `tools/list`.

**Checks:**

1. **Plugin location**: The `cursor_cli` directory (containing `cli.py`) must be inside SMCP’s plugins directory. By default that is `plugins/` inside the SMCP repo (or the path set by `MCP_PLUGINS_DIR`).
2. **Name**: The directory must be named `cursor_cli` (so SMCP discovers it as plugin name `cursor_cli`).
3. **cli.py**: There must be a `cli.py` in that directory, and it should be executable (`chmod +x plugins/cursor_cli/cli.py`).
4. **Restart**: Restart SMCP after adding or changing the plugin. Check SMCP logs for “Discovered plugin: cursor_cli”.

---

## cursor_cli__start fails: command not found

**Symptom:** Tool returns something like “Cursor CLI command not found: agent” (or the value of `cmd`).

**Checks:**

1. **Cursor CLI installed**: Install Cursor CLI (see [Prerequisites](PREREQUISITES.md#2-cursor-cli--non-interactive-print-mode)). Ensure the binary (e.g. `agent` or `cursor-agent`) is on the **PATH of the user/process that runs SMCP**.
2. **Correct command name**: If your install uses a different command (e.g. `cursor-agent`), set `CURSOR_CLI_CMD=cursor-agent` or pass `cmd: "cursor-agent"` in the tool call.
3. **Same environment**: If SMCP runs under systemd or another environment, that environment may have a different PATH. Set `CURSOR_CLI_CMD` to the full path to the binary if needed (e.g. `/usr/local/bin/agent`).

---

## Workspace trust prompt / run exits immediately

**Symptom:** Cursor CLI exits right away and the output file contains a message about “Workspace Trust Required” or “Pass --trust”.

**Fix:** The plugin already adds `--trust` to the command. If you still see this, ensure you’re using the latest plugin version. If Cursor CLI changes its flags, the plugin may need to be updated to pass the new trust flag.

---

## status always returns “running” or never “completed”

**Symptom:** You poll `cursor_cli__status` but `run_status` never becomes `completed` or `failed`.

**Checks:**

1. **Correct agent_uid**: Use the exact `agent_uid` returned from `cursor_cli__start`. Copy-paste or pass it through without changing it.
2. **Same sessions_dir**: If you passed `sessions_dir` to `start`, pass the same value to `status` and `output`. Otherwise the plugin looks in the default directory and won’t find the session files.
3. **Process and exitcode**: The plugin writes `.exitcode` when the wrapper process exits. If the Cursor CLI process hangs, the wrapper may still be running; check the host (e.g. `ps`) to see if the agent process is alive. If the run is stuck, you may need to kill the process and treat it as a failed run.

---

## output returns “No output file for agent_uid”

**Symptom:** `cursor_cli__output` returns an error saying no output file exists for that `agent_uid`.

**Checks:**

1. **agent_uid**: Use the same `agent_uid` returned from `cursor_cli__start` (or `cursor_cli_docker__start`).
2. **sessions_dir**: Use the same `sessions_dir` as for `start` (or rely on the same default). If SMCP runs in a different environment (e.g. different user or container), the default may point to different directories for start vs. output.
   - **cursor_cli** default: `~/.cursor/smcp-sessions`
   - **cursor_cli_docker** default: `~/.cursor/smcp-docker-sessions`
   Always pass the `sessions_dir` returned by `start` into `output` so both use the same path.
3. **Timing**: The output file is created when the run starts. If `start` failed (e.g. command not found, Docker image missing), the file may never be created. Check the `start` result for `status: "error"`.
4. **cursor_cli_docker**: The in-container runner creates the output file at the start of the run. If you still see "No output file", the error message includes the path that was checked; ensure that matches the `sessions_dir` from `start`.

---

## Session files left behind

Session files (`.txt`, `.pid`, `.exitcode`) are kept in `sessions_dir` (default `~/.cursor/smcp-sessions`). They are not auto-deleted. You can:

- Periodically delete old files (e.g. by `agent_uid` or by modification time).
- Point `CURSOR_CLI_SESSIONS_DIR` to a directory that is cleaned by another process or script.

---

## cursor_cli_docker: permission denied on Docker socket

**Symptom:** `cursor_cli_docker__build` or `cursor_cli_docker__start` returns “permission denied while trying to connect to the docker API at unix:///var/run/docker.sock”.

**Cause:** When the agent is used through **Letta**, Letta spawns the SMCP process. That process often does not run with the `docker` group, so it cannot access the Docker socket.

**Fix:** Run SMCP via a wrapper that has Docker access and point Letta’s MCP server config at that wrapper. Full steps (wrapper script, Letta API config, attaching tools): **[Letta + Docker access](LETTA_DOCKER_ACCESS.md)**.

---

## More help

- **SMCP**: [github.com/sanctumos/smcp](https://github.com/sanctumos/smcp) — server logs, plugin discovery, and run behavior.
- **Cursor CLI**: [cursor.com/docs/cli/overview](https://cursor.com/docs/cli/overview) — install, modes, and flags.
- **Operational model**: [CURSOR_CLI_OPERATIONAL_MODEL.md](CURSOR_CLI_OPERATIONAL_MODEL.md) — how the plugin runs the agent and manages session files.

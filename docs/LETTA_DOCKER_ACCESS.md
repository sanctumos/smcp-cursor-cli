# Letta + SMCP: Docker access for cursor_cli_docker

When the **cursor_cli_docker** plugin is used with SMCP and the agent is run through **Letta**, tool calls (`cursor_cli_docker__build`, `cursor_cli_docker__start`, etc.) can fail with:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

This happens because **Letta spawns the SMCP process itself** (via its MCP server config). That process runs as the Letta user and often does **not** have the `docker` group, so it cannot access the Docker socket even if the host user is in `docker`.

---

## Fix: run SMCP with docker group when Letta invokes it

The SMCP process that handles tool calls must run with access to the Docker socket. Two ways to achieve that:

1. **Use a wrapper script** that runs `sg docker -c "python3 smcp_stdio.py"` and configure Letta’s MCP server to run that script instead of `python3 smcp_stdio.py` directly.
2. **Run the Letta server (or the user that runs it)** with the `docker` group so any SMCP subprocess inherits it (only if that fits your setup).

Recommended approach is (1): keep one canonical wrapper and point Letta at it.

---

## 1. Wrapper script (in the SMCP server directory)

On the host where SMCP and Letta run, create a script in the **SMCP server tree** (same directory as `smcp_stdio.py` or the SMCP repo root). Example path: `/path/to/sanctum/smcp/run-with-docker.sh`.

An example script is in this repo: **docs/run-with-docker.sh.example**. Copy it into your SMCP server directory and adjust paths if needed.

**Contents:**

```bash
#!/bin/bash
# Wrapper so SMCP runs with docker group when invoked by Letta (stdio).
# Letta spawns this script; we run smcp_stdio.py under sg docker so the
# cursor_cli_docker plugin can access the Docker socket.
set -e
cd "$(dirname "$0")"
ENV_FILE="../env.letta"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a
exec sg docker -c "exec python3 smcp_stdio.py"
```

- Adjust `ENV_FILE` if your Letta/env file lives elsewhere (e.g. same dir as `smcp_stdio.py`).
- Make it executable: `chmod +x run-with-docker.sh`.

---

## 2. Configure Letta to use the wrapper

Letta’s MCP server for SMCP is configured with a **command** and **args** (e.g. `command: /usr/bin/python3`, `args: [smcp_stdio.py]`). That process is the one that runs the plugins and needs Docker access.

**Update the MCP server** so Letta runs the wrapper instead of Python directly:

- **Command:** full path to the wrapper, e.g. `/home/<your-user>/sanctum/smcp/run-with-docker.sh`
- **Args:** `[]` (empty)
- **Env:** keep existing env (e.g. `MCP_PLUGINS_DIR`, `VENICE_API_KEY`) so the wrapper’s child process still gets them.

**Via Letta API (self‑hosted):**

```bash
# Get your auth token (e.g. from ~/.letta/.env or Letta admin).
export LETTA_BASE_URL="http://your-letta-host:8284"
export LETTA_API_KEY="your-token"

# PATCH the SMCP MCP server (use the id from GET /v1/mcp-servers/).
curl -s -X PATCH \
  -H "Authorization: Bearer $LETTA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "mcp_server_type": "stdio",
      "command": "/home/<your-user>/sanctum/smcp/run-with-docker.sh",
      "args": [],
      "env": {
        "MCP_PLUGINS_DIR": "/home/<your-user>/sanctum/smcp/plugins",
        "VENICE_API_KEY": "your-venice-key-if-needed"
      }
    }
  }' \
  "$LETTA_BASE_URL/v1/mcp-servers/mcp_server-<YOUR_SMCP_SERVER_ID>"
```

Preserve your existing `config.env` when building the PATCH body; only `command` and `args` need to change to the wrapper path and `[]`.

After updating, Letta will use the wrapper the next time it starts the SMCP process (e.g. new conversation or reconnect). Then `cursor_cli_docker__build` and `cursor_cli_docker__start` should be able to reach the Docker socket.

---

## 3. Attach tools to the agent (Letta API)

After the plugin can talk to Docker, ensure the **cursor_cli_docker** and **delay** tools are attached to the agent’s profile:

1. **Refresh MCP server tools** (so Letta has the latest tool list, including `cursor_cli_docker__*` and `delay__sleep`):
   - `PATCH /v1/mcp-servers/{mcp_server_id}/refresh`
2. **List tools** for that MCP server: `GET /v1/mcp-servers/{mcp_server_id}/tools`
3. **Attach** each needed tool to the agent: `PATCH /v1/agents/{agent_id}/tools/attach/{tool_id}`

Tools to attach for full Docker + delay support:

- `cursor_cli_docker__build`
- `cursor_cli_docker__start`
- `cursor_cli_docker__status`
- `cursor_cli_docker__output`
- `cursor_cli_docker__stop`
- `delay__sleep`

---

## Cursor authentication (no output / exit 1)

If the Cursor CLI is **not authenticated on the host**, agent runs can exit with code 1 and **produce no stdout/stderr**. The container mounts the host's `~/.cursor` and `~/.config/cursor`; if those lack valid auth, the Cursor CLI inside the container has nothing to use.

**Fix:** On the host where SMCP runs, log in once: run `agent` interactively (e.g. in a terminal) and complete any login flow. After that, the container's mounted auth dirs will have credentials and runs can produce output. The plugin also appends a hint to **output** when the run failed and no output was captured, so the agent at least sees that auth may be the cause.

### Auth when SMCP runs as a different user

If SMCP is invoked by Letta and runs as a **different user** than the one who ran `agent login` (e.g. Letta runs as `letta` but you logged in as `alice`), the plugin will mount that process user's `~/.cursor` and `~/.config/cursor` — which are empty. Set these in the env that the wrapper sources (e.g. in `env.letta`) so the container mounts the correct auth dirs:

- **`CURSOR_CONFIG_HOST_DIR`** — Host path to the **logged-in** user's `.cursor` dir (e.g. `/home/alice/.cursor`).
- **`CURSOR_XDG_CONFIG_DIR`** — Host path to that user's `.config/cursor` (e.g. `/home/alice/.config/cursor`).

Optional if the binary is only in that user's home:

- **`CURSOR_CLI_HOST_PATH`** — Full path to the `agent` binary (e.g. `/home/alice/.local/bin/agent`).
- **`CURSOR_AGENT_HOST_DIR`** — Path to that user's `.local/share/cursor-agent` (e.g. `/home/alice/.local/share/cursor-agent`).

Then (re)start or reconnect the MCP server so the new process picks up the env; the next container run will have valid auth.

---

## Summary

| Problem | Letta runs SMCP as its own subprocess; that process doesn’t have `docker` group → permission denied on `/var/run/docker.sock`. |
|--------|----------------------------------------------------------------------------------------------------------------------------------|
| Fix    | Run SMCP via a wrapper that does `sg docker -c "python3 smcp_stdio.py"` and set Letta’s MCP server **command** to that wrapper, **args** to `[]`. |
| Then   | Refresh MCP tools and attach `cursor_cli_docker__*` and `delay__sleep` to the agent so the agent can build the image and run containers. |
| No output | If runs exit with code 1 and empty output, ensure Cursor is authenticated on the host (run `agent` once interactively). If SMCP runs as a different user, set `CURSOR_CONFIG_HOST_DIR` and `CURSOR_XDG_CONFIG_DIR` in the wrapper env (see "Auth when SMCP runs as a different user" above). Use `cursor_cli_docker__stop` to stop/remove a container. |

# cursor_cli_docker

**SMCP plugin to run Cursor CLI in non-interactive (headless) mode — inside a Docker container.** Functionally identical to `cursor_cli`, but every agent run is sandboxed: the spawned Cursor agent gets root inside an ephemeral container with full dev tooling while the production host stays untouched.

---

## Why this variant?

| | `cursor_cli` | `cursor_cli_docker` |
|---|---|---|
| Agent runs as | Host process | Container process (root inside) |
| Host filesystem | Full access | Only mounted workspace + sessions |
| Risk of host damage | Real | Contained — kill the container |
| Package installs | Hit the host | Scoped to ephemeral container |

Use this plugin whenever agent runs might install packages, modify system files, or otherwise do things you wouldn't want on a production box.

---

## Prerequisites

Everything from the base `cursor_cli` plugin, plus:

- **Docker** installed and the SMCP host user able to run `docker` commands.
- The **sandbox image** built (see Quick Start below).
- **Cursor CLI authenticated on the host.** The container mounts the host's `~/.cursor` and `~/.config/cursor` for auth. If Cursor is not logged in on the host, the agent run can exit with code 1 and **no output**. Run `agent` once interactively on the host (or copy valid auth into those dirs) so the container has credentials.
- **If the agent runs via Letta:** the SMCP process that Letta spawns must have Docker socket access. By default Letta runs `python3 smcp_stdio.py` directly, which often does not have the `docker` group. Use a wrapper script and configure Letta’s MCP server to run it — see [Letta + Docker access](../../docs/LETTA_DOCKER_ACCESS.md).

---

## Quick start

### 1. Build the sandbox image

```bash
# From SMCP repo root (after installing this plugin)
python plugins/cursor_cli_docker/cli.py build
```

Or call the MCP tool: `cursor_cli_docker__build`.

### 2. Install into SMCP

```bash
cp -r /path/to/plugins/cursor_cli_docker  plugins/
chmod +x plugins/cursor_cli_docker/cli.py
# Restart SMCP
```

### 3. Use

Call `cursor_cli_docker__start` with a `prompt`. Poll with `cursor_cli_docker__status`. Retrieve with `cursor_cli_docker__output`. Identical workflow to the non-Docker variant.

---

## Tools

| Tool | Description |
|------|-------------|
| `cursor_cli_docker__build` | Build/rebuild the sandbox Docker image |
| `cursor_cli_docker__start` | Start a Cursor agent run inside a container |
| `cursor_cli_docker__status` | Check run status (running / completed / failed) |
| `cursor_cli_docker__output` | Read the agent's output text |
| `cursor_cli_docker__stop` | Stop and remove the container for an agent_uid (kill a run or clean up) |

---

## How it works

1. **`start`** writes the prompt to `{sessions_dir}/{uid}.prompt`, then runs `docker run -d` with:
   - The workspace directory mounted at `/workspace` (read-write).
   - The sessions directory mounted at `/sessions` (read-write).
   - The host's Cursor CLI binary (full path) and data dir mounted read-only; the runner is invoked with this path so the container does not need the binary on `PATH`.
   - The host's `~/.cursor` and `~/.config/cursor` mounted for auth (or `CURSOR_CONFIG_HOST_DIR` / `CURSOR_XDG_CONFIG_DIR` if set).
   - A small Python runner script (`_runner.py`) that reads the prompt file and runs the agent with `--trust --sandbox disabled --yolo` (unrestricted execution; the container is the sandbox).
2. **`status`** runs `docker inspect` on the named container to check state and exit code.
3. **`output`** reads `{sessions_dir}/{uid}.txt` from the host (shared volume). You can call it while the run is still in progress to get output so far (streaming).

**Long-running runs (e.g. browser automation):** Output is written incrementally. The in-container runner pipes the agent’s stdout/stderr through a writer that flushes after each line, and uses `stdbuf -oL -eL` so the agent’s output is line-buffered. That way `cursor_cli_docker__output` shows progress during the run instead of only after the process exits.

Each container is named `smcp_agent_{uid}` so multiple runs can coexist.

---

## Configuration

All settings come from environment variables or tool arguments. Tool arguments take priority.

| Env var | Default | Description |
|---------|---------|-------------|
| `CURSOR_DOCKER_IMAGE` | `smcp-cursor-sandbox` | Docker image for agent containers |
| `CURSOR_CLI_CMD` | `agent` | Cursor CLI command name inside container |
| `CURSOR_CLI_WORKSPACE` | *(none)* | Default workspace directory on host |
| `CURSOR_CLI_SESSIONS_DIR` | `~/.cursor/smcp-docker-sessions` | Session file storage |
| `CURSOR_CLI_HOST_PATH` | *(auto-detect)* | Host path to cursor CLI binary (passed to runner so container can exec it) |
| `CURSOR_AGENT_HOST_DIR` | *(auto-detect)* | Host path to cursor-agent data |
| `CURSOR_CONFIG_HOST_DIR` | `~/.cursor` | Host path to cursor config (auth) |
| `CURSOR_XDG_CONFIG_DIR` | `~/.config/cursor` | Host path to cursor XDG config (auth tokens) |
| `CURSOR_CLI_MODEL` | `composer-2` | Cursor model ID passed as `--model` to the agent (default avoids deprecated `auto`). |

---

## Container cleanup

Containers are **not** auto-removed so you can inspect them after failure. To clean up finished containers:

```bash
docker rm $(docker ps -a --filter "name=smcp_agent_" --filter "status=exited" -q)
```

---

## License

- **Code**: AGPL-3.0 — see [LICENSE](../../LICENSE).
- **Documentation**: CC BY-SA 4.0 — see [LICENSE-DOCS](../../LICENSE-DOCS).

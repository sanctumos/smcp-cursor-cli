# smcp-cursor-cli

**SMCP plugin to run Cursor CLI in non-interactive (headless) mode.** Start agent runs, poll their status, and retrieve output—designed for use with **Sanctum Tasks heartbeat** and the **Model Context Protocol (MCP)**.

---

## Table of contents

- [What this is](#what-this-is)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [License](#license)

---

## What this is

- **An SMCP plugin**: runs inside an [SMCP](https://github.com/sanctumos/smcp) (MCP) server and exposes three tools: `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output`.
- **Cursor CLI in non-interactive mode**: launches Cursor’s `agent -p "<prompt>"` (print mode) in the background so long-running tasks don’t block MCP. Output is written to session files; status and output are polled by the caller.
- **Agent UID**: each run gets a unique `agent_uid` so multiple Cursor agents can run in parallel and be polled independently.
- **Sanctum Tasks**: the intended pattern is for the calling agent to create a **heartbeat-queue task** that polls `cursor_cli__status` until the run is `completed` or `failed`, then calls `cursor_cli__output` and uses the result.

---

## Prerequisites

You must have the following in place before using this plugin.

### 1. SMCP (MCP server)

**This plugin runs only as part of an SMCP server.** SMCP is the Sanctum/Animus MCP server that discovers and runs plugins.

- **Repository**: [sanctumos/smcp](https://github.com/sanctumos/smcp)
- **Role**: Discovers plugins in its `plugins/` directory, exposes their commands as MCP tools (e.g. `cursor_cli__start`), and runs plugin CLIs via subprocess.
- **Setup**: Clone and run SMCP (see [SMCP documentation](https://github.com/sanctumos/smcp) and [Getting started](docs/GETTING_STARTED.md#smcp-setup)). This plugin is **installed by copying (or symlinking) into SMCP’s `plugins/` directory**.

Without SMCP, this repo is only a plugin implementation; there is no standalone MCP server here.

### 2. Cursor CLI (non-interactive mode)

Cursor CLI provides the `agent` (or `cursor-agent`) command used by this plugin in **non-interactive (print) mode** only.

- **Install**: [Cursor CLI documentation](https://cursor.com/docs/cli/overview) — e.g. `curl https://cursor.com/install -fsS | bash` (macOS/Linux/WSL).
- **Relevant mode**: **Non-interactive (print) mode** — `agent -p "<prompt>" --output-format text`. Used for scripts, CI, and automation; runs to completion and prints to stdout. Interactive and cloud modes are not used by this plugin.
- **Behavior**: The plugin runs `agent -p "..." --output-format text --trust` in the background and captures stdout to a session file.

You need Cursor CLI installed and on `PATH` (or set `CURSOR_CLI_CMD` / pass `cmd` to the tool) on the machine where SMCP runs.

### 3. MCP (Model Context Protocol)

MCP is the protocol that lets AI clients (e.g. Letta, Cursor IDE) discover and call tools provided by servers like SMCP.

- **Context**: SMCP is an MCP server; this plugin adds **tools** to that server. Clients connect to SMCP (SSE or STDIO), call `tools/list`, and see `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output`. They then call `tools/call` with the tool name and arguments.
- **No extra setup**: If you already run SMCP and connect your client to it, MCP is in use. This plugin simply adds more tools to that server.

For more detail on how SMCP, Cursor CLI, and MCP fit together, see [Prerequisites](docs/PREREQUISITES.md).

---

## Quick start

1. **Install and run SMCP** (see [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)).
2. **Install Cursor CLI** and ensure `agent` (or your `CURSOR_CLI_CMD`) is on `PATH`.
3. **Install this plugin** into SMCP:
   ```bash
   # From SMCP repo root
   cp -r /path/to/smcp-cursor-cli/plugins/cursor_cli plugins/
   chmod +x plugins/cursor_cli/cli.py
   ```
4. **Restart SMCP.** The tools `cursor_cli__start`, `cursor_cli__status`, and `cursor_cli__output` will appear in `tools/list`.
5. **Use from your agent**: Call `cursor_cli__start` with a `prompt`; use the returned `agent_uid` in a heartbeat task that polls `cursor_cli__status` until completed, then calls `cursor_cli__output`. See [Sanctum Tasks integration](docs/SANCTUM_TASKS.md) and [Tools reference](docs/TOOLS_REFERENCE.md).

---

## Documentation

Full documentation is in the **[docs/](docs/README.md)** directory. Summary:

| Document | Description |
|----------|-------------|
| [**Prerequisites**](docs/PREREQUISITES.md) | **SMCP**, **Cursor CLI**, and **MCP** — what they are, where to get them, and why they’re required |
| [**Getting started**](docs/GETTING_STARTED.md) | Step-by-step setup: SMCP, Cursor CLI, installing the plugin |
| [**Configuration**](docs/CONFIGURATION.md) | Environment variables, tool arguments, and optional overrides |
| [**Tools reference**](docs/TOOLS_REFERENCE.md) | `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output` — parameters and examples |
| [**Sanctum Tasks integration**](docs/SANCTUM_TASKS.md) | Using the plugin with the heartbeat queue |
| [**Operational model**](docs/CURSOR_CLI_OPERATIONAL_MODEL.md) | Design: non-interactive mode, agent UID, poll-and-retrieve |
| [**Troubleshooting**](docs/TROUBLESHOOTING.md) | Common issues and fixes |

See [docs/README.md](docs/README.md) for the full documentation index.

---

## License

- **Code**: GNU Affero General Public License v3 (AGPL-3.0) — see [LICENSE](LICENSE).
- **Documentation and other non-code content**: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) — see [LICENSE-DOCS](LICENSE-DOCS).

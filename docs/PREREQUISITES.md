# Prerequisites

This plugin depends on **SMCP** (the MCP server), **Cursor CLI** (non-interactive mode), and **MCP** (the protocol). This document explains what each is and how to satisfy the prerequisites.

---

## 1. SMCP — the MCP server

### What it is

**SMCP** is the Sanctum/Animus **Model Context Protocol (MCP) server**. It:

- Discovers plugins in a `plugins/` directory (each plugin has a `cli.py`).
- Exposes each plugin’s commands as **MCP tools** (e.g. `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output`).
- Runs plugin CLIs via subprocess when a client calls a tool.
- Supports **SSE** (for Letta and other HTTP clients) and **STDIO** (for Cursor IDE and other local clients).

**smcp-cursor-cli is a plugin for SMCP.** It does not run on its own; it must be installed into an SMCP server’s `plugins/` directory.

### Where to get it

- **Repository**: [github.com/sanctumos/smcp](https://github.com/sanctumos/smcp)
- Clone the repo, install its dependencies, and run the server (see SMCP’s README and [Getting started](GETTING_STARTED.md#smcp-setup) in this repo).

### Why it’s required

Without SMCP, there is no MCP server to host this plugin. Clients (Letta, Cursor, etc.) talk to SMCP; SMCP discovers and runs plugins like this one.

---

## 2. Cursor CLI — non-interactive (print) mode

### What it is

**Cursor CLI** is the terminal interface for Cursor’s AI agent. It can run in:

- **Interactive mode**: conversational; requires user input. **Not used by this plugin.**
- **Non-interactive (print) mode**: single prompt, runs to completion, prints to stdout. **This is what the plugin uses.**

Relevant commands (from [Cursor CLI docs](https://cursor.com/docs/cli/overview)):

```bash
# Non-interactive — used by this plugin
agent -p "find and fix performance issues" --model "gpt-5.2"
agent -p "review these changes for security issues" --output-format text
```

The plugin runs the equivalent of:

```bash
agent -p "<your prompt>" --output-format text --trust
```

in the background and captures stdout to a session file.

### Where to get it

- **Documentation**: [cursor.com/docs/cli/overview](https://cursor.com/docs/cli/overview)
- **Install** (examples from Cursor docs):
  - **macOS / Linux / WSL**: `curl https://cursor.com/install -fsS | bash`
  - **Windows PowerShell**: `irm 'https://cursor.com/install?win32=true' | iex`

After install, the command is typically `agent` (or `cursor-agent` on some setups). Ensure it’s on `PATH` on the machine where SMCP runs.

### Why it’s required

This plugin is a bridge between MCP (tools) and Cursor CLI (agent runs). If Cursor CLI is not installed or not on `PATH`, `cursor_cli__start` will fail with a “command not found” style error.

---

## 3. MCP — Model Context Protocol

### What it is

**MCP (Model Context Protocol)** is the protocol that lets AI applications discover and call tools provided by servers. In this setup:

- **SMCP** = MCP server (exposes tools).
- **Client** = Letta, Cursor IDE, or another MCP client that connects to SMCP and calls `tools/list` and `tools/call`.
- **This plugin** = adds three tools to SMCP: `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output`.

You don’t install “MCP” as a separate product; you use a client that supports MCP and point it at SMCP. SMCP and this plugin then provide the tools over MCP.

### How it fits

1. You run **SMCP** (with this plugin in `plugins/`).
2. Your **MCP client** (e.g. Letta) connects to SMCP (SSE or STDIO).
3. The client calls **tools/list** and sees `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output`.
4. The client calls **tools/call** with name `cursor_cli__start` and arguments (e.g. `prompt`); SMCP runs `plugins/cursor_cli/cli.py start --prompt "..."` and returns the result (including `agent_uid`).
5. The client (or a heartbeat task) then calls `cursor_cli__status` and `cursor_cli__output` with that `agent_uid`.

For more on the protocol, see [modelcontextprotocol.io](https://modelcontextprotocol.io/).

---

## Summary

| Prerequisite | Purpose | Where |
|--------------|---------|--------|
| **SMCP** | MCP server that loads and runs this plugin | [github.com/sanctumos/smcp](https://github.com/sanctumos/smcp) |
| **Cursor CLI** | Provides `agent -p "..."` in non-interactive mode | [cursor.com/docs/cli/overview](https://cursor.com/docs/cli/overview) |
| **MCP** | Protocol used by SMCP and your client | Used automatically when you connect a client to SMCP |

Next: [Getting started](GETTING_STARTED.md) for step-by-step setup.

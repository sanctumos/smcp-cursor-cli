# Documentation index

Documentation for **smcp-cursor-cli**: setup, configuration, tools, and integration.

---

## Prerequisites and setup

| Document | Description |
|----------|-------------|
| [**PREREQUISITES**](PREREQUISITES.md) | **SMCP**, **Cursor CLI**, **MCP**, and **Sanctum Tasks** (heartbeat) — what they are, where to get them, and why they’re required. Start here if you’re new to the stack. |
| [**GETTING_STARTED**](GETTING_STARTED.md) | Step-by-step: install and run SMCP, install Cursor CLI, install this plugin, verify tools, and first use. |

---

## Configuration and usage

| Document | Description |
|----------|-------------|
| [**CONFIGURATION**](CONFIGURATION.md) | Environment variables, tool arguments, optional hardcoded overrides, and session directory layout. |
| [**TOOLS_REFERENCE**](TOOLS_REFERENCE.md) | Full reference for `cursor_cli__start`, `cursor_cli__status`, and `cursor_cli__output`: parameters, behavior, and example results. |
| [**SANCTUM_TASKS**](SANCTUM_TASKS.md) | Using the plugin with Sanctum Tasks heartbeat queue: non-blocking polling and output retrieval. |

---

## Design and troubleshooting

| Document | Description |
|----------|-------------|
| [**CURSOR_CLI_OPERATIONAL_MODEL**](CURSOR_CLI_OPERATIONAL_MODEL.md) | Operational model: non-interactive mode, agent UID, poll-and-retrieve, and configuration rules. |
| [**TROUBLESHOOTING**](TROUBLESHOOTING.md) | Common issues: plugin not discovered, command not found, trust prompt, status/output problems, and session files. |

---

## Other

| Document | Description |
|----------|-------------|
| [**RESEARCH_SMCP_UCW**](RESEARCH_SMCP_UCW.md) | Research notes on SMCP and UCW used during plugin design (reference). |

---

**Quick links to prerequisites**

- **SMCP (MCP server)**: [github.com/sanctumos/smcp](https://github.com/sanctumos/smcp)
- **Cursor CLI**: [cursor.com/docs/cli/overview](https://cursor.com/docs/cli/overview)
- **MCP**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)
- **Sanctum Tasks (heartbeat)**: [github.com/sanctumos/sanctum-tasks](https://github.com/sanctumos/sanctum-tasks)

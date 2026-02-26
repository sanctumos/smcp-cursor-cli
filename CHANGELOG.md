# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.0.2] - 2025-02-26

### Added

- **plugins/cursor_cli/cli.py**: Full SMCP plugin implementation.
  - `--describe`: Returns plugin spec with commands start, status, output and parameter schemas.
  - **start**: Launches Cursor CLI with `agent -p "<prompt>" --output-format text --trust` in background; creates session dir, writes PID and output file; returns `agent_uid`. Config: prompt (required), workspace, cmd, sessions_dir (arg or env).
  - **status**: Takes `agent_uid` (and optional sessions_dir). Returns `run_status`: `running` | `completed` | `failed`; writes exit code to `<agent_uid>.exitcode` when process ends.
  - **output**: Takes `agent_uid`; returns contents of `<agent_uid>.txt`.
- Config resolution: argument overrides env var; defaults from `_overrides.get_default_*`.
- **plugins/cursor_cli/README.md**: Usage and configuration for the plugin.

### Changed

- Start command adds `--trust` so non-interactive runs do not block on workspace trust prompt.

---

## [0.0.1] - 2025-02-26

### Added (planning)

- **Repository setup**
  - Cloned `sanctumos/smcp-cursor-cli`; added `tmp/` to `.gitignore` for reference repos.
  - Cloned SMCP (`sanctumos/smcp`) and UCW (`actuallyrizzn/ucw`) into `tmp/` for research and plugin design.

- **Documentation**
  - **docs/RESEARCH_SMCP_UCW.md**: Research summary for SMCP plugin discovery, tool execution, and UCW behavior; design decisions (Sanctum Tasks heartbeat, non-interactive only, agent UID, argument-or-env configuration).
  - **docs/CURSOR_CLI_OPERATIONAL_MODEL.md**: Operational model for MCP integration: Sanctum Tasks heartbeat integration (beta), non-interactive-only assumption, agent UID requirement, start/status/output tool contract, configuration rule (argument overrides env var), session management, and execution options (screen/tmux/nohup).

- **Licensing**
  - **LICENSE**: Code under GNU Affero General Public License v3 (AGPL-3.0).
  - **LICENSE-DOCS**: All other IP (documentation, data, non-code) under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
  - README updated with license summary.

- **Configuration and overrides**
  - Design rule: any variable (API key, CLI command, workspace, session dir) may be supplied by tool argument or environment variable; argument overrides env.
  - **plugins/cursor_cli/_overrides.py**: Constant-override section at top of codebase (commented out) for optional hardcoded defaults; not recommended, but available for users who prefer it.

### Design decisions (for implementation)

- Plugin integrates with **Sanctum Tasks heartbeat** (beta): calling agent creates a heartbeat-queue task to poll Cursor CLI status until completed, then retrieve output.
- All runs use **Cursor CLI non-interactive (print) mode** only (`agent -p "..."`).
- **Agent UID** is captured at start and used for all status/output polling; multiple concurrent agents supported.
- Tool contract: `cursor_cli__start` (returns `agent_uid`), `cursor_cli__status(agent_uid)`, `cursor_cli__output(agent_uid)`.

---

[0.0.2]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.0.2
[0.0.1]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.0.1

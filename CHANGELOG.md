# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- **Letta + Docker access** — Documentation for using cursor_cli_docker when the agent runs via Letta.
  - **docs/LETTA_DOCKER_ACCESS.md**: Why “permission denied” on Docker socket occurs (Letta spawns SMCP without docker group), fix via wrapper script (`sg docker -c "python3 smcp_stdio.py"`), PATCH Letta MCP server config to run the wrapper, and attaching tools to the agent.
  - **docs/run-with-docker.sh.example**: Example wrapper script to copy into the SMCP server directory.
  - **plugins/cursor_cli_docker/README.md**: Prerequisites now mention Letta and link to LETTA_DOCKER_ACCESS.md.
  - **docs/TROUBLESHOOTING.md**: New section “cursor_cli_docker: permission denied on Docker socket” with link to LETTA_DOCKER_ACCESS.md.
  - **docs/README.md**: Doc index updated with LETTA_DOCKER_ACCESS.

---

## [0.2.0] - 2026-03-07

### Added

- **cursor_cli_docker** — Docker-sandboxed variant of the Cursor CLI plugin.
  - Same tool contract as `cursor_cli`: `start`, `status`, `output` (plus `build` for the sandbox image).
  - Every agent run executes inside an ephemeral Docker container with root access in-container; host is isolated.
  - Mounts workspace (rw), sessions dir, host Cursor CLI binary + auth (`~/.cursor`, `~/.config/cursor`), optional git config.
  - Dockerfile (Ubuntu 24.04, Node 20, Python 3, dev tools), `_overrides.py` for image/path config, README.

---

## [0.1.0] - 2025-02-25

### Added

- **Sanctum Tasks (heartbeat coordination)** as an explicit prerequisite.
  - **README.md**: New prerequisite §4 — heartbeat coordination with Sanctum Tasks; repo link, role (heartbeat queue), why required (MCP timeouts vs long Cursor runs); doc index table updated.
  - **docs/PREREQUISITES.md**: New section 4 — Sanctum Tasks (what it is, where to get it, why required); summary table updated.
  - **docs/README.md**: Prerequisites row and quick links updated to include Sanctum Tasks.

---

## [0.0.4] - 2025-02-26

### Added

- **Documentation suite**
  - **docs/README.md**: Documentation index and quick links to SMCP, Cursor CLI, MCP.
  - **docs/PREREQUISITES.md**: SMCP (repo, role, why required), Cursor CLI (non-interactive mode, install), MCP (protocol, how it fits).
  - **docs/GETTING_STARTED.md**: Step-by-step SMCP setup, Cursor CLI install/verify, plugin install, verification, first use.
  - **docs/CONFIGURATION.md**: Environment variables, tool arguments, precedence, optional overrides, session directory layout.
  - **docs/TOOLS_REFERENCE.md**: Full reference for `cursor_cli__start`, `cursor_cli__status`, `cursor_cli__output` (parameters, behavior, example results).
  - **docs/SANCTUM_TASKS.md**: Heartbeat-queue integration and intended usage.
  - **docs/TROUBLESHOOTING.md**: Plugin not discovered, command not found, trust prompt, status/output issues, session files.
- **README.md**: Comprehensive rewrite — what this is, prerequisites (SMCP, Cursor CLI, MCP) with conspicuous links, quick start, documentation table, license.

---

## [0.0.3] - 2025-02-26

### Added

- **Test suite** (unit, integration, e2e) with ≥80% coverage.
  - **Unit** (`tests/unit/`): `get_plugin_description`, `_resolve_*`, `run_start` (mocked and real fake agent), `run_status`, `run_output`, `main()` (describe, no-command, start, status, output), exception paths (Popen failure, OSError on output read, invalid exitcode file).
  - **Integration** (`tests/integration/`): CLI as subprocess (`python -m plugins.cursor_cli`), `--describe`, start with nonexistent cmd, full start/status/output with fake agent, status/output error cases.
  - **E2E** (`tests/e2e/`): Full flow start → status (until completed) → output; output readable while run is still running.
- **requirements-test.txt**: pytest, pytest-cov.
- **pytest.ini**: testpaths, coverage source/omit/fail_under=80.
- **tests/README.md**: How to run tests and coverage.
- **plugins/__init__.py**: Package marker for imports.

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

[0.2.0]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.2.0
[0.1.0]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.1.0
[0.0.4]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.0.4
[0.0.3]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.0.3
[0.0.2]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.0.2
[0.0.1]: https://github.com/sanctumos/smcp-cursor-cli/releases/tag/v0.0.1

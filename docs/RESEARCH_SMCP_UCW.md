# SMCP & UCW Research Summary

Research notes for building a headless SMCP plugin for Cursor CLI. Both repos are in `tmp/` for reference.

**Design decisions**: (1) Plugin is used with **Sanctum Tasks heartbeat** (beta); (2) all agent runs use **non-interactive mode only**; (3) the calling agent should create a **heartbeat-queue task** to poll status until completed; (4) **agent UID** is captured at start and used for all status/output polling (multiple agents = multiple UIDs). See [CURSOR_CLI_OPERATIONAL_MODEL.md](CURSOR_CLI_OPERATIONAL_MODEL.md).

---

## 1. SMCP (sanctumos/smcp)

### What It Is

- **MCP server** for the Animus/Letta/Sanctum ecosystem
- **Plugin-based**: discovers plugins in `plugins/` (or `MCP_PLUGINS_DIR`)
- **Transports**: SSE (HTTP) for Letta, STDIO for headless/CLI clients
- **Protocol**: JSON-RPC 2.0, Model Context Protocol compliant

### Plugin Discovery

1. Scans `plugins/<name>/` for `cli.py`
2. **Preferred**: runs `python cli.py --describe` → expects JSON:
   ```json
   {
     "plugin": { "name", "version", "description" },
     "commands": [
       {
         "name": "command-name",
         "description": "...",
         "parameters": [
           { "name", "type", "description", "required", "default" }
         ]
       }
     ]
   }
   ```
3. **Fallback**: runs `python cli.py --help` and scrapes "Available commands:" section (no param schemas)

### Tool Naming

- Format: `plugin__command` (double underscore)
- Legacy: `plugin.command` (dot) still supported
- Rationale: Claude Desktop requires `^[a-zA-Z0-9_-]{1,64}$`

### Tool Execution

- SMCP runs: `python cli.py <command> --arg1 val1 --arg2 val2 ...`
- Args: underscores → dashes (`use_ssl` → `--use-ssl`)
- Booleans: `true` → `--flag` only
- Arrays: each element passed as `--arg item`
- **Timeout**: 300 seconds default
- **Output**: plugin must print JSON to stdout; SMCP returns it as tool result

### Plugin Structure (Required)

```
plugins/my_plugin/
├── __init__.py     # optional
├── cli.py          # required - main entry, must be executable
├── README.md       # recommended
└── requirements.txt # optional
```

### Key Files

- `smcp.py` – SSE server, plugin discovery, tool registration
- `smcp_stdio.py` – STDIO transport for headless use (e.g. Cursor)
- `discover_plugins()` – finds `plugins/*/cli.py`
- `get_plugin_describe()` – runs `--describe`, parses JSON
- `execute_plugin_tool()` – subprocess execution with arg mapping

---

## 2. UCW (actuallyrizzn/ucw)

### What It Is

- **Universal Command Wrapper** – parses `--help` / `man` / `/?` and generates:
  - In-memory Python wrappers
  - Full MCP plugin files (SMCP-compatible)
- **Zero deps** (stdlib only)
- **Dual use**: SMCP plugin (wrap/parse/execute) + standalone dev tool

### Commands (SMCP Plugin Mode)

| Command | Purpose |
|---------|---------|
| `wrap <cmd>` | Parse command help, generate wrapper (JSON or file) |
| `parse <cmd>` | Parse help only, return spec as JSON |
| `execute <cmd> --args a b --options '{"--flag": true}'` | Run command with args |

### As SMCP Plugin

- Copy `ucw/` into `smcp/plugins/`
- UCW **does not** implement `--describe` in its main `cli.py`
- UCW's `wrapper_builder.py` has `describe()` and generates plugins *with* `--describe`
- So: UCW is a *meta-plugin* – it wraps arbitrary commands and can emit new SMCP plugins

### UCW Flow

1. **Parse**: run `command --help` (or `man command` on POSIX), parse output
2. **Spec**: build `CommandSpec` (name, positional_args, options)
3. **Wrapper**: `build_wrapper(spec)` → `CommandWrapper.run(*args, **kwargs)`
4. **Plugin gen**: `generate_mcp_plugin_code(spec)` → full `cli.py` with `--describe`

### Key Insight for Cursor CLI

UCW can **wrap** `cursor` the same way it wraps `ls` or `gh`. The generated plugin would:
- Have `--describe` (full param schemas)
- Have a single `run` command that forwards to `cursor`
- Be a drop-in SMCP plugin

**Caveat**: UCW assumes the command has `--help` or similar. Cursor CLI may need custom handling if its help format differs.

---

## 3. Cursor CLI (External)

- Not installed in this workspace (proot/Android)
- User reports Cursor CLI is installed on their Windows machine
- **Headless** use case: run Cursor CLI from an MCP client (e.g. Letta agent) without a GUI
- Need to determine: `cursor --help` output, subcommands, and how to drive it programmatically

---

## 4. Build Strategy for smcp-cursor-cli

### Option A: UCW-Generated Plugin

1. Run UCW on Cursor CLI (where it’s installed):  
   `ucw wrap cursor --output plugins/cursor_cli/cli.py`
2. Add `--describe` if UCW output doesn’t include it
3. Ship as SMCP plugin

**Pros**: Minimal code, auto param schemas  
**Cons**: Depends on Cursor’s help format; may need tweaks

### Option B: Hand-Written Plugin

1. Create `plugins/cursor_cli/` with custom `cli.py`
2. Implement `--describe` with known Cursor CLI commands/params
3. Subprocess to `cursor <subcommand> ...` with proper arg mapping

**Pros**: Full control, can handle odd CLI behavior  
**Cons**: More work, manual schema maintenance

### Option C: Hybrid

1. Use UCW to parse Cursor CLI and get initial spec
2. Hand-edit the generated plugin for edge cases
3. Add any Cursor-specific logic (e.g. streaming, auth)

---

## 5. Next Steps

1. **Capture Cursor CLI surface**: Run `cursor --help` and `cursor <subcmd> --help` on a machine where it’s installed; document subcommands and args
2. **Choose strategy**: A, B, or C based on Cursor’s help format
3. **Implement plugin**: Create `plugins/cursor_cli/` in smcp-cursor-cli (or in smcp’s plugins dir)
4. **Test**: Run SMCP with the plugin, verify tools appear and execute correctly
5. **STDIO vs SSE**: For Cursor IDE integration, STDIO (`smcp_stdio.py`) is likely the right transport

---

## 6. Related Docs

- **[CURSOR_CLI_OPERATIONAL_MODEL.md](CURSOR_CLI_OPERATIONAL_MODEL.md)** – How to run Cursor CLI as a long-running, pollable process for MCP (background + poll + retrieve).

---

## 7. File Locations

| Item | Path |
|------|------|
| SMCP repo | `tmp/smcp/` |
| UCW repo | `tmp/ucw/` |
| SMCP plugins dir | `tmp/smcp/plugins/` |
| Plugin dev guide | `tmp/smcp/docs/plugin-development-guide.md` |
| UCW wrapper builder | `tmp/ucw/generator/wrapper_builder.py` |

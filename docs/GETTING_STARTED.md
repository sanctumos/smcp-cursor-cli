# Getting started

Step-by-step setup so you can run the smcp-cursor-cli plugin inside SMCP and use it from an MCP client.

---

## 1. SMCP setup

### 1.1 Clone and install SMCP

SMCP is the MCP server that will host this plugin. You must have it running first.

```bash
git clone https://github.com/sanctumos/smcp.git
cd smcp
# Create a virtual environment and install dependencies (see SMCP’s README)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

See the [SMCP repository](https://github.com/sanctumos/smcp) for the latest install and run instructions (e.g. `python smcp.py` for SSE, or `python smcp_stdio.py` for STDIO).

### 1.2 Confirm SMCP runs

Start SMCP and ensure it binds (e.g. `http://127.0.0.1:8000` for SSE, or STDIO). You can leave it running; we’ll add the plugin next.

---

## 2. Cursor CLI setup

### 2.1 Install Cursor CLI

On the same machine (or the machine that will run SMCP), install Cursor CLI so the `agent` command is available.

**macOS / Linux / WSL:**

```bash
curl https://cursor.com/install -fsS | bash
```

**Windows (PowerShell):**

```powershell
irm 'https://cursor.com/install?win32=true' | iex
```

See [Cursor CLI documentation](https://cursor.com/docs/cli/overview) for up-to-date install steps.

### 2.2 Verify non-interactive mode

```bash
agent -p "list files in current directory" --output-format text
```

If this runs and prints output (or asks for trust the first time), Cursor CLI is set up. The plugin adds `--trust` so non-interactive runs don’t block on trust prompts.

---

## 3. Install the smcp-cursor-cli plugin

### 3.1 Copy the plugin into SMCP

From your SMCP clone:

```bash
# Replace /path/to/smcp-cursor-cli with the path to this repo
cp -r /path/to/smcp-cursor-cli/plugins/cursor_cli /path/to/smcp/plugins/
chmod +x /path/to/smcp/plugins/cursor_cli/cli.py
```

Or use a symlink:

```bash
cd /path/to/smcp/plugins
ln -s /path/to/smcp-cursor-cli/plugins/cursor_cli .
```

### 3.2 Optional: custom plugins directory

If SMCP is configured to use a different plugins directory (e.g. via `MCP_PLUGINS_DIR`), copy or link `cursor_cli` into that directory instead.

### 3.3 Restart SMCP

Restart the SMCP server so it discovers the new plugin. Check logs for a line like “Discovered plugin: cursor_cli”.

---

## 4. Verify the plugin

### 4.1 Describe (optional)

From the plugin directory:

```bash
cd /path/to/smcp-cursor-cli/plugins/cursor_cli
python cli.py --describe
```

You should see JSON with `plugin.name` `"cursor_cli"` and three commands: `start`, `status`, `output`.

### 4.2 Via MCP (tools/list)

Connect your MCP client to SMCP and call **tools/list**. You should see tools named:

- `cursor_cli__start`
- `cursor_cli__status`
- `cursor_cli__output`

---

## 5. Use from your agent

1. Call **cursor_cli__start** with a `prompt` (and optional `workspace`, `cmd`, `sessions_dir`). The result includes **agent_uid**.
2. Create a **heartbeat task** (e.g. with Sanctum Tasks) that:
   - Calls **cursor_cli__status** with that `agent_uid` until `run_status` is `completed` or `failed`.
   - Then calls **cursor_cli__output** with the same `agent_uid` to get the run output.
3. Use the output in your agent’s next steps (e.g. memory, another tool).

See [Tools reference](TOOLS_REFERENCE.md) for parameters and [Sanctum Tasks integration](SANCTUM_TASKS.md) for the heartbeat pattern.

---

## Next steps

- [Configuration](CONFIGURATION.md) — environment variables and tool arguments
- [Tools reference](TOOLS_REFERENCE.md) — full parameter and behavior details
- [Sanctum Tasks integration](SANCTUM_TASKS.md) — heartbeat-queue usage

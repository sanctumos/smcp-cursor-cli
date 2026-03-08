# delay — SMCP plugin

**Standalone delay/sleep tool.** Packaged with smcp-cursor-cli; install as its own plugin so agents can pause N seconds without ending the turn (e.g. before checking cursor_cli_docker status).

## Tool

| Tool | Description |
|------|-------------|
| `delay__sleep` | Sleep for `seconds` (1–3600), then return. |

## Install

Copy or symlink this directory into your SMCP `plugins/`:

```bash
ln -s /path/to/smcp-cursor-cli/plugins/delay /path/to/smcp/plugins/delay
chmod +x /path/to/smcp/plugins/delay/cli.py
```

Restart SMCP.

## Usage

Call `delay__sleep` with `seconds` (integer). Example: sleep 30 seconds before polling again.

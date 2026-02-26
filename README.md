# smcp-cursor-cli

SMCP plugin to run Cursor CLI agents in non-interactive mode and poll their status/output. For use with **Sanctum Tasks heartbeat** (beta): the calling agent creates a heartbeat task that polls until the Cursor agent completes, then retrieves output. All runs use Cursor’s non-interactive mode only. Each run has an **agent UID** so multiple agents can be tracked and polled independently.

See [docs/CURSOR_CLI_OPERATIONAL_MODEL.md](docs/CURSOR_CLI_OPERATIONAL_MODEL.md) for the full operational model.

## License

- **Code**: GNU Affero General Public License v3 (AGPL-3.0) — see [LICENSE](LICENSE).
- **All other IP** (documentation, data, and non-code content): Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) — see [LICENSE-DOCS](LICENSE-DOCS).
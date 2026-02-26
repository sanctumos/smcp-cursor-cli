# Sanctum Tasks integration

This plugin is designed to be used with **Sanctum Tasks** heartbeat functions (beta). The idea is to avoid blocking the main agent on long Cursor CLI runs: you start a run, then a **heartbeat-queue task** polls status until the run is done and retrieves the output.

---

## Why use the heartbeat queue

- **MCP timeouts**: SMCP typically times out long tool calls (e.g. 300 seconds). A Cursor agent task can run much longer.
- **Non-blocking**: Instead of one long `cursor_cli__start` call that waits for completion, you:
  1. Call `cursor_cli__start` once → get `agent_uid` and return immediately.
  2. Enqueue a **heartbeat task** that runs periodically and checks `cursor_cli__status` for that `agent_uid`.
  3. When the heartbeat task sees `completed` or `failed`, it calls `cursor_cli__output` and stores or returns the result for the main agent.

So the main agent does not block; the heartbeat task does the polling in the background.

---

## Intended usage

1. **Main agent** calls **cursor_cli__start** with the desired `prompt` (and optional `workspace`, `cmd`, `sessions_dir`).
2. **Main agent** receives `agent_uid` in the result.
3. **Main agent** creates a **Sanctum Tasks** task that runs on the **heartbeat queue**, with instructions like:
   - “Poll `cursor_cli__status` for `agent_uid` until `run_status` is `completed` or `failed`.”
   - “When done, call `cursor_cli__output` for that `agent_uid` and store the result (e.g. in memory or a resource the main agent can read).”
4. **Heartbeat task** runs on a schedule, calls `cursor_cli__status`, and when the run is finished calls `cursor_cli__output` and completes the task.
5. **Main agent** can later use that output (e.g. from memory or a follow-up tool) for its next steps.

Sanctum Tasks and the exact heartbeat API are documented in the [Sanctum Tasks](https://github.com/sanctumos/sanctum-tasks) repository.

---

## Multiple agents

You can start several Cursor CLI runs at once; each has a distinct **agent_uid**. The heartbeat task (or tasks) must poll using the correct **agent_uid** for each run. Always pass the `agent_uid` returned from `cursor_cli__start` into `cursor_cli__status` and `cursor_cli__output`.

---

## Summary

- **Start** → get `agent_uid`.
- **Create a heartbeat task** that polls **status** by `agent_uid` until completed/failed, then calls **output** and stores the result.
- **Main agent** uses the stored output when the heartbeat task is done.

For tool parameters and examples, see [Tools reference](TOOLS_REFERENCE.md).

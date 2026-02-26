# Cursor CLI Operational Model for MCP Integration

Research on how to integrate Cursor CLI with SMCP given MCP's constraints: no streaming read, no long-blocking tool calls, need for poll-and-retrieve output.

---

## Integration: Sanctum Tasks Heartbeat (Beta)

**This plugin is designed to be used with the heartbeat functions of [Sanctum Tasks](https://github.com/sanctumos/sanctum-tasks), a current beta product for the Sanctum Suite.**

- All agent runs from this SMCP plugin use **non-interactive mode only** (`agent -p "..."`). Interactive mode is not supported.
- **Intended usage**: The agent (e.g. Letta) that uses this plugin should **create a Sanctum Tasks task that sits in the heartbeat queue** to periodically check the status of the Cursor CLI task until it is completed. The heartbeat task polls `cursor_cli__status` (and when complete, calls `cursor_cli__output`) so the main agent does not block.
- **Agent UID**: Multiple Cursor CLI agents can be running at once; each has a distinct **agent UID**. The plugin must **capture and return the agent UID** when starting an agent. All polling (`status`, `output`) is scoped by this agent UID so the heartbeat task checks the correct run.

### Configuration: arguments and environment variables

Any value that might vary by environment (API keys, CLI command/path, workspace, session directory, etc.) must be **flexible in source**:

- **Option A**: Passed as a **tool argument** from the agent (e.g. the agent sends `workspace` or `api_key` in the tool call).
- **Option B**: Set as an **environment variable** (e.g. `CURSOR_CLI_WORKSPACE`, `CURSOR_CLI_CMD`).

Preference: **argument overrides environment variable** when both are present. This allows Sanctum’s own environment variable system for MCP to supply defaults (e.g. per-server or per-project env), while the agent can still override per call when needed. Implement so that both paths are supported for every such variable.

Variables that follow this rule (argument or env) include, at minimum:

- CLI command/binary (e.g. `agent` vs `cursor-agent`)
- Workspace/cwd for the agent run
- Session/output directory (where we write `<agent_uid>.txt`, `.pid`)
- Any API key or token the CLI or plugin might need later

---

## 1. MCP / SMCP Constraints

- **No streaming**: MCP tool calls are request→response. The server cannot "read" what the user sees in a terminal in real time.
- **Timeout**: SMCP defaults to 300s per tool call. Long-running agent tasks will exceed this.
- **Blocking**: A tool that blocks until the agent finishes would hold the MCP connection open and likely time out.
- **Output**: The calling agent (e.g. Letta) needs the result as text it can consume. That text must come from a file, stdout capture, or API—not from watching a live terminal.

---

## 2. Cursor CLI Modes (from docs)

**This plugin uses only non-interactive (print) mode.** Interactive mode is not supported.

### Interactive mode (not used by this plugin)

```bash
agent
agent "refactor the auth module to use JWT tokens"
```

- Conversational, TTY-based
- Requires user input (approve commands, answer questions)
- Not used by smcp-cursor-cli

### Non-interactive (print) mode — plugin default

```bash
agent -p "find and fix performance issues" --model "gpt-5.2"
agent -p "review these changes for security issues" --output-format text
```

- Designed for "scripts, CI pipelines, or automation"
- Runs with a single prompt
- `--output-format text` for plain text output
- **Assumption**: Runs to completion, prints to stdout, then exits

### Cloud Agent

```bash
agent -c "refactor the auth module and add comprehensive tests"
```

- Runs in Cursor's cloud
- Status/results via cursor.com/agents or API
- Different architecture; not local subprocess

---

## 3. Session Storage (from cli-continues)

| Item | Location |
|------|----------|
| Cursor sessions | `~/.cursor/projects/*/agent-transcripts/*.jsonl` |
| Format | JSONL: `{"role":"user|assistant","message":{"content":[...]}}` |

- Transcripts are written as the session runs
- Can be read to get conversation history and agent output
- Requires parsing JSONL and extracting text from `message.content`

---

## 4. Operational Model: Background + Poll + Retrieve

Because MCP can't block on long tasks, use a **fire-and-forget + poll** pattern:

### Architecture

```
┌─────────────────┐     start-agent      ┌──────────────────┐
│  MCP Client     │ ──────────────────►  │  SMCP Plugin     │
│  (Letta, etc.)  │                      │  (cursor_cli)    │
│                 │  ◄──────────────────  │                  │
│                 │  session_id, status   │  Launches agent  │
└─────────────────┘                      │  in screen/tmux  │
        │                                 │  stdout → file   │
        │  status-agent                   └────────┬─────────┘
        │  get-output-agent                         │
        ▼                                          ▼
┌─────────────────┐                      ┌──────────────────┐
│  Poll until     │                      │  screen -dmS      │
│  done or        │                      │  agent -p "..."   │
│  timeout        │                      │  > /tmp/out.txt   │
└─────────────────┘                      └──────────────────┘
```

### Tool design

| Tool | Purpose |
|------|---------|
| `cursor_cli__start` | Run `agent -p "<prompt>"` in screen/tmux, capture stdout to a session file. **Returns `agent_uid`** (and optionally session_id) so polling can target this run. |
| `cursor_cli__status` | **Takes `agent_uid`.** Check if that agent is still running; return `running` / `completed` / `failed`. |
| `cursor_cli__output` | **Takes `agent_uid`.** Read the output file for that agent; return contents (or partial if still running). |

Multiple agents can be running at once; every operation that targets a specific run is keyed by **agent_uid**.

### Agent UID requirement

- When we start an agent, Cursor CLI (or our launcher) must provide or we must assign a **unique agent UID** for that run.
- `cursor_cli__start` must **capture and return this agent_uid** in its JSON output.
- `cursor_cli__status` and `cursor_cli__output` both take `agent_uid` so the caller (e.g. a Sanctum Tasks heartbeat task) can poll the correct agent.
- If Cursor CLI does not expose an agent UID, we generate one (e.g. UUID) at start and store output/PID keyed by that UID.

### Session management

- **Agent UID**: Unique per run; returned from `start`, used for all `status` and `output` calls.
- **Output file**: `~/.cursor/smcp-sessions/<agent_uid>.txt` (or similar)
- **PID file**: `~/.cursor/smcp-sessions/<agent_uid>.pid` for status checks
- **Screen/tmux**: `screen -dmS cursor-<agent_uid> agent -p "..." --output-format text 2>&1 | tee <output_file>`

### Flow (with Sanctum Tasks heartbeat)

1. Agent calls `cursor_cli__start` with prompt → gets **`agent_uid`** (and any session_id).
2. Agent **creates a Sanctum Tasks task** that runs on the heartbeat queue: "poll `cursor_cli__status` for `agent_uid` until completed, then call `cursor_cli__output` and store/return result."
3. Heartbeat task runs periodically, calls `cursor_cli__status(agent_uid)` → gets `running` or `completed`.
4. When `completed`, heartbeat task calls `cursor_cli__output(agent_uid)` → gets full output, then marks the task done or feeds result back.
5. Main agent can later use that output (e.g. from memory or a follow-up tool).

---

## 5. Alternative: Agent Transcripts

Instead of (or in addition to) stdout capture:

- Run agent in a known workspace (e.g. `--cwd /path/to/project`)
- After start, poll `~/.cursor/projects/<workspace>/agent-transcripts/` for new/modified JSONL files
- Parse JSONL to extract assistant messages
- Return latest assistant content as the "output"

**Pros**: Captures full conversation, including streaming-style updates  
**Cons**: JSONL parsing, need to map session_id to transcript file, format more complex

---

## 6. Execution Environment Options

### Option A: screen (simplest)

```bash
screen -dmS "cursor-${SESSION_ID}" bash -c "agent -p '${PROMPT}' --output-format text 2>&1 | tee ${OUTPUT_FILE}; echo \$? > ${EXIT_CODE_FILE}"
```

- Detached session
- stdout + stderr to file
- Exit code in separate file for status

### Option B: tmux

```bash
tmux new-session -d -s "cursor-${SESSION_ID}" "agent -p '${PROMPT}' --output-format text 2>&1 | tee ${OUTPUT_FILE}; echo \$? > ${EXIT_CODE_FILE}"
```

- Same idea as screen
- Use whichever is available

### Option C: Docker

- Run Cursor CLI in a container with workspace mounted
- Isolates environment
- More setup; may need Cursor auth inside container

### Option D: nohup + background

```bash
nohup agent -p "${PROMPT}" --output-format text > "${OUTPUT_FILE}" 2>&1 &
echo $! > "${PID_FILE}"
```

- Simpler than screen/tmux
- Need to poll PID for completion

---

## 7. Open Questions

1. **Non-interactive mode behavior**: Does `agent -p "..."` block until the task is fully done? Or does it return when the first "response" is ready? Docs say "scripts and CI" so blocking is likely.
2. **Partial output**: Can we read the output file while the agent is still running to stream progress? (e.g. `tail -f` or periodic read)
3. **Agent approval**: In non-interactive mode, does the agent auto-approve commands, or does it hang waiting for input?
4. **Workspace**: Does `agent -p "..."` need a `--cwd` or `-C` to run in a specific directory? Need to verify.
5. **Command name**: Is it `agent`, `cursor`, or `cursor-agent`? ccmanager uses `cursor-agent`; docs use `agent`. May vary by install.

---

## 8. Recommended Next Steps

1. **Verify non-interactive mode** on a machine with Cursor CLI:
   - Run `agent -p "list files in current directory" --output-format text`
   - Confirm it blocks until done and prints to stdout
   - Check if it requires any approvals or prompts

2. **Implement minimal plugin**:
   - `start`: launch in screen with output to file
   - `status`: check PID or screen session
   - `output`: read output file

3. **Test with long task**: Run a 2–3 minute task, poll status, verify output is captured correctly.

4. **Add transcript parsing** (optional): If stdout is insufficient, parse `~/.cursor/projects/*/agent-transcripts/` for richer output.

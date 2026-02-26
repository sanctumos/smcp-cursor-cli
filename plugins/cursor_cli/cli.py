#!/usr/bin/env python3
"""
SMCP plugin: Cursor CLI (non-interactive mode).
Start agent runs, poll status, retrieve output. For use with Sanctum Tasks heartbeat.
Copyright (c) 2025 SanctumOS. SPDX-License-Identifier: AGPL-3.0
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

# Config: argument overrides env, else defaults from _overrides
try:
    from ._overrides import get_default_cmd, get_default_workspace, get_default_sessions_dir
except ImportError:
    from _overrides import get_default_cmd, get_default_workspace, get_default_sessions_dir


def get_plugin_description() -> Dict[str, Any]:
    """Return structured plugin description for SMCP --describe."""
    return {
        "plugin": {
            "name": "cursor_cli",
            "version": "0.0.1",
            "description": "Run Cursor CLI in non-interactive mode; start, poll status, retrieve output. For Sanctum Tasks heartbeat.",
        },
        "commands": [
            {
                "name": "start",
                "description": "Start a Cursor CLI agent run with the given prompt. Returns agent_uid for status/output polling.",
                "parameters": [
                    {"name": "prompt", "type": "string", "description": "Task prompt for the agent", "required": True, "default": None},
                    {"name": "workspace", "type": "string", "description": "Working directory for the agent (optional)", "required": False, "default": None},
                    {"name": "cmd", "type": "string", "description": "Cursor CLI command (e.g. agent or cursor-agent)", "required": False, "default": None},
                    {"name": "sessions_dir", "type": "string", "description": "Directory for session output and PID files", "required": False, "default": None},
                ],
            },
            {
                "name": "status",
                "description": "Check whether the agent run is still running or completed.",
                "parameters": [
                    {"name": "agent_uid", "type": "string", "description": "Agent UID returned from start", "required": True, "default": None},
                    {"name": "sessions_dir", "type": "string", "description": "Sessions directory (optional)", "required": False, "default": None},
                ],
            },
            {
                "name": "output",
                "description": "Read the output of a completed or in-progress agent run.",
                "parameters": [
                    {"name": "agent_uid", "type": "string", "description": "Agent UID returned from start", "required": True, "default": None},
                    {"name": "sessions_dir", "type": "string", "description": "Sessions directory (optional)", "required": False, "default": None},
                ],
            },
        ],
    }


def _resolve_sessions_dir(arg_value: Optional[str]) -> str:
    return arg_value if arg_value else get_default_sessions_dir()


def _resolve_cmd(arg_value: Optional[str]) -> str:
    return arg_value if arg_value else get_default_cmd()


def _resolve_workspace(arg_value: Optional[str]) -> Optional[str]:
    if arg_value is not None and arg_value != "":
        return arg_value
    return get_default_workspace()


def run_start(
    prompt: str,
    workspace: Optional[str] = None,
    cmd: Optional[str] = None,
    sessions_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Start agent in background; return agent_uid and paths."""
    sessions_dir = _resolve_sessions_dir(sessions_dir)
    cmd_name = _resolve_cmd(cmd)
    workspace = _resolve_workspace(workspace)

    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)

    agent_uid = uuid.uuid4().hex
    out_path = base / f"{agent_uid}.txt"
    pid_path = base / f"{agent_uid}.pid"
    exitcode_path = base / f"{agent_uid}.exitcode"

    argv = [cmd_name, "-p", prompt, "--output-format", "text", "--trust"]
    env = os.environ.copy()
    cwd = workspace if workspace else None

    def write_exitcode_when_done(proc: subprocess.Popen, path: Path) -> None:
        proc.wait()
        try:
            path.write_text(str(proc.returncode or -1))
        except OSError:
            pass

    try:
        with open(out_path, "w", encoding="utf-8") as out_file:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=out_file,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                env=env,
                start_new_session=True,
            )
        pid_path.write_text(str(proc.pid))
        t = threading.Thread(target=write_exitcode_when_done, args=(proc, exitcode_path), daemon=True)
        t.start()
    except FileNotFoundError:
        return {"status": "error", "error": f"Cursor CLI command not found: {cmd_name}", "agent_uid": agent_uid}
    except Exception as e:
        return {"status": "error", "error": str(e), "agent_uid": agent_uid}

    return {
        "status": "success",
        "agent_uid": agent_uid,
        "message": "Agent started; use status and output with this agent_uid.",
        "sessions_dir": sessions_dir,
    }


def run_status(agent_uid: str, sessions_dir: Optional[str] = None) -> Dict[str, Any]:
    """Return running | completed | failed."""
    sessions_dir = _resolve_sessions_dir(sessions_dir)
    base = Path(sessions_dir)
    pid_path = base / f"{agent_uid}.pid"
    exitcode_path = base / f"{agent_uid}.exitcode"

    if not pid_path.exists():
        return {"status": "success", "agent_uid": agent_uid, "run_status": "failed", "message": "No PID file; run may not have started."}

    try:
        pid = int(pid_path.read_text().strip())
    except (ValueError, OSError):
        return {"status": "success", "agent_uid": agent_uid, "run_status": "failed", "message": "Invalid or unreadable PID file."}

    # Check if process exists (Unix)
    try:
        os.kill(pid, 0)
        return {"status": "success", "agent_uid": agent_uid, "run_status": "running", "message": "Agent is still running."}
    except OSError:
        pass  # process gone

    if exitcode_path.exists():
        try:
            code = int(exitcode_path.read_text().strip())
            run_status = "completed" if code == 0 else "failed"
            return {"status": "success", "agent_uid": agent_uid, "run_status": run_status, "exit_code": code}
        except (ValueError, OSError):
            pass

    return {"status": "success", "agent_uid": agent_uid, "run_status": "completed", "message": "Process ended (exit code unknown)."}


def run_output(agent_uid: str, sessions_dir: Optional[str] = None) -> Dict[str, Any]:
    """Read output file for agent_uid."""
    sessions_dir = _resolve_sessions_dir(sessions_dir)
    base = Path(sessions_dir)
    out_path = base / f"{agent_uid}.txt"

    if not out_path.exists():
        return {"status": "error", "error": f"No output file for agent_uid {agent_uid}", "agent_uid": agent_uid}

    try:
        text = out_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"status": "error", "error": str(e), "agent_uid": agent_uid}

    return {"status": "success", "agent_uid": agent_uid, "output": text}


def main() -> None:
    parser = argparse.ArgumentParser(description="Cursor CLI SMCP plugin (non-interactive mode)")
    parser.add_argument("--describe", action="store_true", help="Output plugin description in JSON format")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # start
    p_start = subparsers.add_parser("start", help="Start an agent run")
    p_start.add_argument("--prompt", required=True, help="Task prompt")
    p_start.add_argument("--workspace", default=None, help="Working directory")
    p_start.add_argument("--cmd", default=None, help="Cursor CLI command (e.g. agent)")
    p_start.add_argument("--sessions-dir", default=None, dest="sessions_dir", help="Sessions directory")

    # status
    p_status = subparsers.add_parser("status", help="Check run status")
    p_status.add_argument("--agent-uid", required=True, dest="agent_uid", help="Agent UID from start")
    p_status.add_argument("--sessions-dir", default=None, dest="sessions_dir", help="Sessions directory")

    # output
    p_output = subparsers.add_parser("output", help="Get run output")
    p_output.add_argument("--agent-uid", required=True, dest="agent_uid", help="Agent UID from start")
    p_output.add_argument("--sessions-dir", default=None, dest="sessions_dir", help="Sessions directory")

    args = parser.parse_args()

    if args.describe:
        print(json.dumps(get_plugin_description(), indent=2))
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result: Dict[str, Any]
    if args.command == "start":
        result = run_start(
            prompt=args.prompt,
            workspace=args.workspace,
            cmd=args.cmd,
            sessions_dir=args.sessions_dir,
        )
    elif args.command == "status":
        result = run_status(agent_uid=args.agent_uid, sessions_dir=args.sessions_dir)
    elif args.command == "output":
        result = run_output(agent_uid=args.agent_uid, sessions_dir=args.sessions_dir)
    else:
        result = {"status": "error", "error": f"Unknown command: {args.command}"}

    print(json.dumps(result))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()

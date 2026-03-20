#!/usr/bin/env python3
"""
SMCP plugin: Cursor CLI — Docker-sandboxed variant.
Functionally identical to cursor_cli but every agent run spawns inside a
Docker container with root access, isolating it from the production host.
Copyright (c) 2025 SanctumOS. SPDX-License-Identifier: AGPL-3.0
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from ._overrides import (
        get_default_cmd,
        get_default_cursor_agent_dir,
        get_default_cursor_config_dir,
        get_default_cursor_host_bin,
        get_default_cursor_xdg_config_dir,
        get_default_image,
        get_default_model,
        get_default_sessions_dir,
        get_default_workspace,
        get_dockerfile_dir,
        get_extra_host_mounts,
    )
except ImportError:
    from _overrides import (
        get_default_cmd,
        get_default_cursor_agent_dir,
        get_default_cursor_config_dir,
        get_default_cursor_host_bin,
        get_default_cursor_xdg_config_dir,
        get_default_image,
        get_default_model,
        get_default_sessions_dir,
        get_default_workspace,
        get_dockerfile_dir,
        get_extra_host_mounts,
    )

CONTAINER_PREFIX = "smcp_agent_"

# ---------------------------------------------------------------------------
# Runner script — written to sessions dir, executed inside the container.
# Avoids all shell-escaping hazards by reading the prompt from a file.
# ---------------------------------------------------------------------------
RUNNER_SCRIPT = r"""#!/usr/bin/env python3
import pathlib, subprocess, sys

uid = sys.argv[1]
cmd = sys.argv[2] if len(sys.argv) > 2 else "agent"
model = (sys.argv[3] if len(sys.argv) > 3 else "").strip()
base = pathlib.Path("/sessions")

prompt = (base / f"{uid}.prompt").read_text(encoding="utf-8")

agent_argv = [cmd, "-p", prompt, "--output-format", "text", "--trust", "--sandbox", "disabled", "--yolo"]
if model:
    agent_argv.extend(["--model", model])
# Force line-buffered stdout/stderr so output appears in the file as the agent prints (not only on exit).
argv = ["stdbuf", "-oL", "-eL", "--"] + agent_argv

out_path = base / f"{uid}.txt"
# Create output file immediately so the host volume has it (avoids "no output file" when agent produces no stdout).
out_path.write_text("", encoding="utf-8")

# Run agent with stdout/stderr piped so we read and flush to file incrementally.
proc = subprocess.Popen(
    argv,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd="/workspace",
    text=True,
    bufsize=1,
)

def copy_stream(stream, path):
    with open(path, "w", encoding="utf-8") as f:
        for line in stream:
            f.write(line)
            f.flush()

copy_stream(proc.stdout, out_path)
proc.wait()
(base / f"{uid}.exitcode").write_text(str(proc.returncode))
sys.exit(proc.returncode)
"""


def _ensure_runner(sessions_dir: str) -> Path:
    """Write the in-container runner script to the sessions volume (idempotent)."""
    runner = Path(sessions_dir) / "_runner.py"
    runner.write_text(RUNNER_SCRIPT, encoding="utf-8")
    return runner


# ---------------------------------------------------------------------------
# Plugin description (--describe)
# ---------------------------------------------------------------------------

def get_plugin_description() -> Dict[str, Any]:
    return {
        "plugin": {
            "name": "cursor_cli_docker",
            "version": "0.3.2",
            "description": (
                "Run Cursor CLI in non-interactive mode inside a Docker container. "
                "Provides start, poll status, retrieve output — sandboxed variant "
                "for Sanctum Tasks heartbeat."
            ),
        },
        "commands": [
            {
                "name": "build",
                "description": "Build (or rebuild) the Docker sandbox image.",
                "parameters": [
                    {"name": "image", "type": "string",
                     "description": "Image name/tag to build", "required": False, "default": None},
                    {"name": "no_cache", "type": "boolean",
                     "description": "Build without Docker cache", "required": False, "default": None},
                ],
            },
            {
                "name": "start",
                "description": (
                    "Start a Cursor CLI agent run inside a Docker container. "
                    "Returns agent_uid for status/output polling."
                ),
                "parameters": [
                    {"name": "prompt", "type": "string",
                     "description": "Task prompt for the agent", "required": True, "default": None},
                    {"name": "workspace", "type": "string",
                     "description": "Host directory to mount as /workspace (rw)", "required": False, "default": None},
                    {"name": "cmd", "type": "string",
                     "description": "Cursor CLI command inside the container", "required": False, "default": None},
                    {"name": "sessions_dir", "type": "string",
                     "description": "Host directory for session files", "required": False, "default": None},
                    {"name": "image", "type": "string",
                     "description": "Docker image to use", "required": False, "default": None},
                    {"name": "model", "type": "string",
                     "description": "Cursor model ID for `agent --model` (e.g. composer-2). Default from CURSOR_CLI_MODEL or composer-2.", "required": False, "default": None},
                ],
            },
            {
                "name": "status",
                "description": "Check whether the containerised agent run is still running or completed.",
                "parameters": [
                    {"name": "agent_uid", "type": "string",
                     "description": "Agent UID returned from start", "required": True, "default": None},
                    {"name": "sessions_dir", "type": "string",
                     "description": "Sessions directory (optional)", "required": False, "default": None},
                ],
            },
            {
                "name": "output",
                "description": "Read the output of a completed or in-progress containerised agent run.",
                "parameters": [
                    {"name": "agent_uid", "type": "string",
                     "description": "Agent UID returned from start", "required": True, "default": None},
                    {"name": "sessions_dir", "type": "string",
                     "description": "Sessions directory (optional)", "required": False, "default": None},
                ],
            },
            {
                "name": "stop",
                "description": "Stop and remove a running container for the given agent_uid. Use to terminate a run or clean up.",
                "parameters": [
                    {"name": "agent_uid", "type": "string",
                     "description": "Agent UID returned from start", "required": True, "default": None},
                    {"name": "sessions_dir", "type": "string",
                     "description": "Sessions directory (optional)", "required": False, "default": None},
                ],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------

def _resolve(arg: Optional[str], fallback):
    return arg if arg else fallback()


# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------

def _docker_available() -> bool:
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=10)
        return True
    except Exception:
        return False


def _image_exists(image: str) -> bool:
    r = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True, timeout=10,
    )
    return r.returncode == 0


def _build_volume_args(sessions_dir: str, workspace: Optional[str]) -> List[str]:
    """Construct -v flags for Docker run."""
    args: List[str] = []

    # Sessions dir — always mounted
    abs_sessions = str(Path(sessions_dir).resolve())
    args += ["-v", f"{abs_sessions}:/sessions"]

    # Workspace — mounted rw so the agent can modify project files
    if workspace:
        abs_ws = str(Path(workspace).resolve())
        args += ["-v", f"{abs_ws}:/workspace"]

    # Cursor CLI binary — resolve symlinks so Docker can mount the real file
    cursor_bin = get_default_cursor_host_bin()
    cursor_bin_resolved = str(Path(cursor_bin).resolve())
    if os.path.isfile(cursor_bin_resolved):
        args += ["-v", f"{cursor_bin_resolved}:{cursor_bin_resolved}:ro"]
        # Also mount the symlink path if different
        if cursor_bin != cursor_bin_resolved:
            parent = str(Path(cursor_bin).parent)
            args += ["-v", f"{parent}:{parent}:ro"]

    # Cursor agent data dir (node runtime, index.js, etc.)
    cursor_data = get_default_cursor_agent_dir()
    if cursor_data and os.path.isdir(cursor_data):
        args += ["-v", f"{cursor_data}:{cursor_data}:ro"]

    # Cursor config dir (~/.cursor) — mount the full directory so the agent
    # has auth, caching, and can write session state inside the container.
    cursor_cfg = get_default_cursor_config_dir()
    if os.path.isdir(cursor_cfg):
        args += ["-v", f"{cursor_cfg}:/root/.cursor"]

    # ~/.config/cursor — holds auth.json with access/refresh tokens
    cursor_xdg = get_default_cursor_xdg_config_dir()
    if os.path.isdir(cursor_xdg):
        args += ["-v", f"{cursor_xdg}:/root/.config/cursor"]

    # Extra user-defined mounts
    for host_path, container_path, mode in get_extra_host_mounts():
        if os.path.exists(host_path):
            args += ["-v", f"{host_path}:{container_path}:{mode}"]

    return args


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def run_build(image: Optional[str] = None, no_cache: bool = False) -> Dict[str, Any]:
    """Build the sandbox Docker image."""
    image = _resolve(image, get_default_image)
    dockerfile_dir = get_dockerfile_dir()

    if not os.path.isfile(os.path.join(dockerfile_dir, "Dockerfile")):
        return {"status": "error", "error": f"Dockerfile not found in {dockerfile_dir}"}

    cmd = ["docker", "build", "-t", image]
    if no_cache:
        cmd.append("--no-cache")
    cmd.append(dockerfile_dir)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            return {"status": "success", "image": image, "message": "Image built successfully."}
        return {"status": "error", "error": proc.stderr[-2000:] if proc.stderr else f"Build exited {proc.returncode}"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Docker build timed out (600s)."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_start(
    prompt: str,
    workspace: Optional[str] = None,
    cmd: Optional[str] = None,
    sessions_dir: Optional[str] = None,
    image: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Start agent inside a Docker container; return agent_uid."""
    sessions_dir = _resolve(sessions_dir, get_default_sessions_dir)
    cmd_name = _resolve(cmd, get_default_cmd)
    workspace = workspace if workspace else get_default_workspace()
    image = _resolve(image, get_default_image)
    model_str = (model or get_default_model()).strip()

    if not _docker_available():
        return {"status": "error", "error": "Docker is not available on this host."}

    if not _image_exists(image):
        return {
            "status": "error",
            "error": (
                f"Docker image '{image}' not found. "
                "Run the 'build' command first: cursor_cli_docker__build"
            ),
        }

    base = Path(sessions_dir)
    base.mkdir(parents=True, exist_ok=True)

    agent_uid = uuid.uuid4().hex
    container_name = f"{CONTAINER_PREFIX}{agent_uid}"

    # Write prompt to a file — the runner reads it, zero shell-escaping risk
    (base / f"{agent_uid}.prompt").write_text(prompt, encoding="utf-8")

    # Ensure the runner script is present in sessions dir
    _ensure_runner(sessions_dir)

    # Assemble Docker command
    volume_args = _build_volume_args(sessions_dir, workspace)

    # Mount git config if it exists so agents can commit
    gitconfig = os.path.expanduser("~/.gitconfig")
    if os.path.isfile(gitconfig):
        volume_args += ["-v", f"{gitconfig}:/root/.gitconfig:ro"]
    git_creds = os.path.expanduser("~/.git-credentials")
    if os.path.isfile(git_creds):
        volume_args += ["-v", f"{git_creds}:/root/.git-credentials:ro"]

    # Pass full path to agent binary so runner finds it (container PATH doesn't have host bin)
    cursor_bin_path = get_default_cursor_host_bin()

    argv = [
        "docker", "run", "-d",
        "--name", container_name,
        *volume_args,
        image,
        "python3", "/sessions/_runner.py", agent_uid, cursor_bin_path, model_str or "",
    ]

    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            return {"status": "error", "error": f"docker run failed: {err}", "agent_uid": agent_uid}
    except Exception as e:
        return {"status": "error", "error": str(e), "agent_uid": agent_uid}

    container_id = proc.stdout.strip()
    # Persist container id for status lookups
    (base / f"{agent_uid}.cid").write_text(container_id, encoding="utf-8")

    return {
        "status": "success",
        "agent_uid": agent_uid,
        "container": container_name,
        "message": (
            "Agent started in Docker container; use status and output with this agent_uid. "
            "Pass the same sessions_dir to cursor_cli_docker__output when retrieving output."
        ),
        "sessions_dir": sessions_dir,
    }


def run_status(agent_uid: str, sessions_dir: Optional[str] = None) -> Dict[str, Any]:
    """Return running | completed | failed for the container."""
    sessions_dir = _resolve(sessions_dir, get_default_sessions_dir)
    container_name = f"{CONTAINER_PREFIX}{agent_uid}"

    # Try docker inspect first
    try:
        proc = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}:{{.State.ExitCode}}", container_name],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as e:
        return {"status": "error", "error": str(e), "agent_uid": agent_uid}

    if proc.returncode != 0:
        # Container not found — check exitcode file (container may have been removed)
        exitcode_path = Path(sessions_dir) / f"{agent_uid}.exitcode"
        if exitcode_path.exists():
            try:
                code = int(exitcode_path.read_text().strip())
                run_status = "completed" if code == 0 else "failed"
                return {"status": "success", "agent_uid": agent_uid, "run_status": run_status, "exit_code": code}
            except (ValueError, OSError):
                pass
        return {
            "status": "success", "agent_uid": agent_uid,
            "run_status": "failed", "message": "Container not found and no exit code recorded.",
        }

    parts = proc.stdout.strip().split(":")
    docker_state = parts[0] if parts else "unknown"
    docker_exit = int(parts[1]) if len(parts) > 1 else -1

    if docker_state == "running":
        return {"status": "success", "agent_uid": agent_uid, "run_status": "running", "message": "Agent container is running."}

    if docker_state == "exited":
        # Prefer the exitcode file written by the runner (reflects agent exit, not container init)
        exitcode_path = Path(sessions_dir) / f"{agent_uid}.exitcode"
        if exitcode_path.exists():
            try:
                code = int(exitcode_path.read_text().strip())
            except (ValueError, OSError):
                code = docker_exit
        else:
            code = docker_exit
        run_status = "completed" if code == 0 else "failed"
        return {"status": "success", "agent_uid": agent_uid, "run_status": run_status, "exit_code": code}

    return {
        "status": "success", "agent_uid": agent_uid,
        "run_status": "failed", "message": f"Container state: {docker_state}",
    }


def run_output(agent_uid: str, sessions_dir: Optional[str] = None) -> Dict[str, Any]:
    """Read output file for agent_uid. When output is empty and exit code is non-zero, append a hint about auth."""
    sessions_dir = _resolve(sessions_dir, get_default_sessions_dir)
    out_path = Path(sessions_dir) / f"{agent_uid}.txt"
    exitcode_path = Path(sessions_dir) / f"{agent_uid}.exitcode"

    if not out_path.exists():
        resolved_dir = str(Path(sessions_dir).resolve())
        return {
            "status": "error",
            "error": (
                f"No output file for agent_uid {agent_uid}. "
                f"Looked in sessions_dir={resolved_dir}. "
                "If you passed sessions_dir to start, pass the same sessions_dir to output."
            ),
            "agent_uid": agent_uid,
            "sessions_dir": resolved_dir,
        }

    try:
        text = out_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"status": "error", "error": str(e), "agent_uid": agent_uid}

    # When no output was captured but the run failed, add a hint so the agent has something to report
    if not text.strip() and exitcode_path.exists():
        try:
            code = int(exitcode_path.read_text().strip())
            if code != 0:
                text = (
                    f"[No stdout/stderr captured. Exit code: {code}. "
                    "Cursor CLI may not be authenticated on the host — ensure the host has valid auth in "
                    "~/.cursor and ~/.config/cursor (mounted into the container). Or the subprocess exited before writing.]"
                )
        except (ValueError, OSError):
            pass

    return {"status": "success", "agent_uid": agent_uid, "output": text}


def run_stop(agent_uid: str, sessions_dir: Optional[str] = None) -> Dict[str, Any]:
    """Stop and remove the container for agent_uid."""
    sessions_dir = _resolve(sessions_dir, get_default_sessions_dir)
    container_name = f"{CONTAINER_PREFIX}{agent_uid}"

    if not _docker_available():
        return {"status": "error", "error": "Docker is not available on this host.", "agent_uid": agent_uid}

    # docker stop then docker rm; rm -f so we remove even if already stopped
    for docker_cmd, args in [
        (["docker", "stop", "-t", "5", container_name], "stop"),
        (["docker", "rm", "-f", container_name], "remove"),
    ]:
        try:
            proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=15)
            if proc.returncode != 0 and "No such container" not in (proc.stderr or ""):
                err = (proc.stderr or proc.stdout or "").strip()
                return {"status": "error", "error": err or f"docker {args} failed", "agent_uid": agent_uid}
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": f"docker {args} timed out", "agent_uid": agent_uid}
        except Exception as e:
            return {"status": "error", "error": str(e), "agent_uid": agent_uid}

    return {
        "status": "success",
        "agent_uid": agent_uid,
        "message": f"Container {container_name} stopped and removed.",
    }


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Cursor CLI SMCP plugin — Docker sandbox variant")
    parser.add_argument("--describe", action="store_true", help="Output plugin description in JSON format")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # build
    p_build = subparsers.add_parser("build", help="Build the sandbox Docker image")
    p_build.add_argument("--image", default=None, help="Image name/tag")
    p_build.add_argument("--no-cache", action="store_true", dest="no_cache", help="Build without cache")

    # start
    p_start = subparsers.add_parser("start", help="Start an agent run in Docker")
    p_start.add_argument("--prompt", required=True, help="Task prompt")
    p_start.add_argument("--workspace", default=None, help="Host workspace to mount")
    p_start.add_argument("--cmd", default=None, help="Cursor CLI command")
    p_start.add_argument("--sessions-dir", default=None, dest="sessions_dir", help="Sessions directory")
    p_start.add_argument("--image", default=None, help="Docker image")
    p_start.add_argument("--model", default=None, help="Cursor model (e.g. composer-2)")

    # status
    p_status = subparsers.add_parser("status", help="Check run status")
    p_status.add_argument("--agent-uid", required=True, dest="agent_uid", help="Agent UID from start")
    p_status.add_argument("--sessions-dir", default=None, dest="sessions_dir", help="Sessions directory")

    # output
    p_output = subparsers.add_parser("output", help="Get run output")
    p_output.add_argument("--agent-uid", required=True, dest="agent_uid", help="Agent UID from start")
    p_output.add_argument("--sessions-dir", default=None, dest="sessions_dir", help="Sessions directory")

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop and remove the container for an agent_uid")
    p_stop.add_argument("--agent-uid", required=True, dest="agent_uid", help="Agent UID from start")
    p_stop.add_argument("--sessions-dir", default=None, dest="sessions_dir", help="Sessions directory")

    args = parser.parse_args()

    if args.describe:
        print(json.dumps(get_plugin_description(), indent=2))
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result: Dict[str, Any]
    if args.command == "build":
        result = run_build(image=args.image, no_cache=args.no_cache)
    elif args.command == "start":
        result = run_start(
            prompt=args.prompt,
            workspace=args.workspace,
            cmd=args.cmd,
            sessions_dir=args.sessions_dir,
            image=args.image,
            model=args.model,
        )
    elif args.command == "status":
        result = run_status(agent_uid=args.agent_uid, sessions_dir=args.sessions_dir)
    elif args.command == "output":
        result = run_output(agent_uid=args.agent_uid, sessions_dir=args.sessions_dir)
    elif args.command == "stop":
        result = run_stop(agent_uid=args.agent_uid, sessions_dir=args.sessions_dir)
    else:
        result = {"status": "error", "error": f"Unknown command: {args.command}"}

    print(json.dumps(result))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()

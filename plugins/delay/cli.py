#!/usr/bin/env python3
"""
SMCP plugin: standalone delay (sleep) tool.
Lets an agent pause for N seconds before checking task status, without ending the turn.
Packaged with smcp-cursor-cli; install into SMCP plugins/ as a separate plugin.
Copyright (c) 2025 SanctumOS. SPDX-License-Identifier: AGPL-3.0
"""

import argparse
import json
import sys
import time
from typing import Any, Dict

MAX_DELAY_SECONDS = 3600  # 1 hour cap


def get_plugin_description() -> Dict[str, Any]:
    return {
        "plugin": {
            "name": "delay",
            "version": "0.1.0",
            "description": (
                "Standalone delay/sleep tool. Sleep for a given number of seconds. "
                "Use when you do not want to end the turn yet—e.g. before checking "
                "cursor_cli_docker status again."
            ),
        },
        "commands": [
            {
                "name": "sleep",
                "description": "Sleep for the given number of seconds, then return. Use before polling task status.",
                "parameters": [
                    {
                        "name": "seconds",
                        "type": "integer",
                        "description": "Number of seconds to sleep (1–3600).",
                        "required": True,
                        "default": None,
                    },
                ],
            },
        ],
    }


def run_sleep(seconds: int) -> Dict[str, Any]:
    """Sleep for the given seconds; return success message."""
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return {"status": "error", "error": "seconds must be an integer"}

    if s < 1:
        return {"status": "error", "error": "seconds must be at least 1"}
    if s > MAX_DELAY_SECONDS:
        return {"status": "error", "error": f"seconds must be at most {MAX_DELAY_SECONDS}"}

    time.sleep(s)
    return {
        "status": "success",
        "message": f"Delayed {s} seconds.",
        "seconds": s,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Delay/sleep SMCP plugin")
    parser.add_argument("--describe", action="store_true", help="Output plugin description in JSON")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    p_sleep = subparsers.add_parser("sleep", help="Sleep for N seconds")
    p_sleep.add_argument("--seconds", type=int, required=True, help="Seconds to sleep (1–3600)")

    args = parser.parse_args()

    if args.describe:
        print(json.dumps(get_plugin_description(), indent=2))
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "sleep":
        result = run_sleep(seconds=args.seconds)
    else:
        result = {"status": "error", "error": f"Unknown command: {args.command}"}

    print(json.dumps(result))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()

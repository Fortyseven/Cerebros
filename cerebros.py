#!/usr/bin/env python3
"""Cerebros CLI entrypoint.

Behavior change: the first non-option token is treated as the command. Global
options (currently only -v/--verbose) must appear before the command name.

Examples:
  cerebro -vv search "some term"
  cerebro example --name Alice
  cerebro search --help
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence, Mapping, Any


import os
from app.cli import CommandContext

# ---------------------------------------------------------------------------
# Global parsing
# ---------------------------------------------------------------------------


def build_global_parser() -> argparse.ArgumentParser:
    import os

    parser = argparse.ArgumentParser(
        prog="cerebro", add_help=False, description="Cerebrosphere CLI"
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (repeat for more)",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        default=os.path.join(os.getcwd(), "workspace"),
        help="Workspace directory (default: ./workspace)",
    )

    parser.add_argument(
        "-nc",
        "--no-color",
        action="store_true",
        help="Disable colored output",
        dest="no_color",
    )

    return parser


# CommandContext now lives in app.cli to avoid circular imports.


# ---------------------------------------------------------------------------
# Dynamic command loading
# ---------------------------------------------------------------------------

try:  # Local import to avoid circular issues on type-check
    from app.commands import load_commands, LoadedCommand  # noqa: WPS433
except Exception:  # pragma: no cover - fallback (no commands available)
    load_commands = lambda: {}  # type: ignore
    LoadedCommand = object  # type: ignore


def print_global_help(
    parser: argparse.ArgumentParser, commands: Mapping[str, Any]
) -> None:
    parser.print_usage()

    print("\nCommands:")

    longest = max((len(name) for name in commands), default=0)

    for name, cmd in sorted(commands.items()):
        print(f"  {name.ljust(longest)}  {cmd.help}")

    print("\nUse 'cerebro <command> --help' for command-specific help.")


def main(argv: list[str] | None = None) -> int:  # noqa: D401 (simple)
    if argv is None:
        argv = sys.argv[1:]

    global_parser = build_global_parser()
    # Use parse_known_args to robustly separate global options from command and its args
    try:
        gns, remainder = global_parser.parse_known_args(argv)
    except SystemExit as e:
        return e.code

    # Set shared workspace state
    import app.state

    app.state.workspace = gns.workspace

    commands = load_commands()

    if gns.help:
        print_global_help(global_parser, commands)
        return 0

    if not remainder:
        print("No command provided.\n")
        print_global_help(global_parser, commands)
        return 1

    command = remainder[0]
    cmd_args = remainder[1:]
    if command not in commands:
        print(f"Unknown command: {command}\n")
        print_global_help(global_parser, commands)
        return 2

    loaded = commands[command]
    # If user asked for per-command help, let parser handle
    if "--help" in cmd_args or "-h" in cmd_args:
        parser = loaded.build_parser(f"cerebro {loaded.name}")
        parser.print_help()
        return 0

    # Create workspace directory if it doesn't exist, but only now
    if gns.workspace and not os.path.exists(gns.workspace):
        os.makedirs(gns.workspace, exist_ok=True)

    parser = loaded.build_parser(f"cerebro {loaded.name}")
    try:
        ns = parser.parse_args(list(cmd_args))
    except SystemExit as e:  # argparse already printed
        return e.code
    handler = loaded.run
    from rich.console import Console

    color_system = None if gns.no_color else "auto"
    console = Console(color_system=color_system)
    ctx = CommandContext(
        verbose=gns.verbose,
        workspace=gns.workspace,
        no_color=gns.no_color,
        console=console,
    )
    try:
        return handler(ctx, ns)
    except SystemExit as e:  # propagate argparse exits inside handler
        return e.code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

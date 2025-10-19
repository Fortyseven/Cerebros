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

# ---------------------------------------------------------------------------
# Global parsing
# ---------------------------------------------------------------------------


def build_global_parser() -> argparse.ArgumentParser:
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
    return parser


class CommandContext:
    """Holds global options available to command handlers."""

    def __init__(self, verbose: int = 0) -> None:
        self.verbose = verbose


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
    # Parse only global flags up to the first non-option token (command)
    # We stop at first arg that does not start with '-'
    global_args: list[str] = []
    remainder: list[str] = []
    for i, token in enumerate(argv):
        if token == "--":
            # Explicit end of options; rest is remainder (command must follow)
            global_args = argv[: i + 1]
            remainder = argv[i + 1 :]
            break
        if token.startswith("-") and token != "-":
            continue
        # First non-option token is command
        global_args = argv[:i]
        remainder = argv[i:]
        break
    else:
        # All tokens were options (or none)
        global_args = argv
        remainder = []

    try:
        gns = global_parser.parse_args(global_args)
    except SystemExit as e:  # argparse already printed message
        return e.code

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

    parser = loaded.build_parser(f"cerebro {loaded.name}")
    try:
        ns = parser.parse_args(list(cmd_args))
    except SystemExit as e:  # argparse already printed
        return e.code
    handler = loaded.run
    ctx = CommandContext(verbose=gns.verbose)
    try:
        return handler(ctx, ns)
    except SystemExit as e:  # propagate argparse exits inside handler
        return e.code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Browse command module.

Provides an interactive TUI (Textual) to explore the workspace and view YAML
entity files. Left pane: directory tree. Right pane: formatted YAML content.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from app.cli import CommandContext


def build_parser(prog: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=prog, description="Browse workspace TUI")
    p.add_argument(
        "--root",
        default=None,
        help="Optional override for root directory (defaults to workspace).",
    )
    return p


def run(ctx: CommandContext, ns: argparse.Namespace) -> int:
    try:
        from app.browse import run_browse_app
    except ImportError:
        ctx.console.print(
            "[red]Textual browse submodule import failed. Is 'textual' installed?[/red]"
        )
        return 1

    root_dir = ns.root or ctx.workspace
    if not root_dir or not os.path.isdir(root_dir):
        ctx.console.print(f"[red]Invalid root directory: {root_dir!r}")
        return 1
    run_browse_app(root_dir)
    return 0


@dataclass
class _Command:
    name: str = "browse"
    help: str = "Browse workspace in an interactive TUI"
    build_parser = staticmethod(build_parser)
    run = staticmethod(run)


COMMAND = _Command()

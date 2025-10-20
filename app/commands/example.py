"""Example command module."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from app.cli import CommandContext


def build_parser(prog: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=prog, description="Run example action")
    p.add_argument("--name", default="world", help="Name to greet")
    return p


def run(ctx: CommandContext, ns: argparse.Namespace) -> int:
    import app.state

    if ctx.verbose:
        print(f"[debug] Running example with name={ns.name}")
        print(f"[debug] Workspace (from ctx): {ctx.workspace}")
        print(f"[debug] Workspace (from app.state): {app.state.workspace}")
    print(f"Hello, {ns.name}!")
    return 0


@dataclass
class _Command:
    name: str = "example"
    help: str = "Run example action"
    build_parser = staticmethod(build_parser)
    run = staticmethod(run)


COMMAND = _Command()

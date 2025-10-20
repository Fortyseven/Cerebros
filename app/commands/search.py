"""Search command module."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from app.cli import CommandContext


def build_parser(prog: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=prog, description="Search the knowledge base")
    p.add_argument("term", help="Search term (quotes allowed by shell)")
    return p


def run(ctx: CommandContext, ns: argparse.Namespace) -> int:
    import app.state

    if ctx.verbose:
        print(f"[debug] Searching for term={ns.term!r}")
        print(f"[debug] Workspace (from ctx): {ctx.workspace}")
        print(f"[debug] Workspace (from app.state): {app.state.workspace}")
    print(f"(stub) Would search for: {ns.term}")
    return 0


@dataclass
class _Command:
    name: str = "search"
    help: str = "Search the knowledge base"
    build_parser = staticmethod(build_parser)
    run = staticmethod(run)


COMMAND = _Command()

"""Search command module."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from app.cli import CommandContext


def build_parser(prog: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=prog, description="Search the knowledge base")
    p.add_argument("term", help="Search term (quotes allowed by shell)")
    p.add_argument(
        "-fp",
        "--full-path",
        action="store_true",
        help="Show absolute file paths in results instead of relative paths.",
    )
    p.add_argument(
        "-l", "--lines", action="store_true", help="Show line numbers in results."
    )
    return p


def run(ctx: CommandContext, ns: argparse.Namespace) -> int:
    import app.state
    import os
    from rich.text import Text

    if ctx.verbose:
        print(f"[debug] Searching for term={ns.term!r}")
        print(f"[debug] Workspace (from ctx): {ctx.workspace}")
        print(f"[debug] Workspace (from app.state): {app.state.workspace}")

    workspace = ctx.workspace or app.state.workspace
    if not workspace:
        print("[error] No workspace directory specified.")
        return 1

    # Recursively find all .yml files in the workspace
    yml_files = []
    for root, dirs, files in os.walk(workspace):
        for file in files:
            if file.endswith(".yml"):
                yml_files.append(os.path.join(root, file))

    if ctx.verbose:
        print(f"[debug] Found {len(yml_files)} YAML files.")
        for f in yml_files:
            print(f"[debug]   {f}")

    # Search for term in values and report line numbers
    console = ctx.console
    found_any = False
    term = ns.term.lower()
    for yml_file in yml_files:
        try:
            with open(yml_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            console.print(f"[warn] Could not read {yml_file}: {e}", style="yellow")
            continue
        matches = []
        last_key = None
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val == "":
                    last_key = key
                else:
                    # Simple key: value
                    if term in val.lower():
                        matches.append((idx, key, val))
                    last_key = None
            elif stripped.startswith("- "):
                # List item
                item = stripped[2:].strip()
                if term in item.lower():
                    matches.append((idx, last_key, item))
        if matches:
            found_any = True
            if getattr(ns, "full_path", False):
                file_path = os.path.abspath(yml_file)
            else:
                file_path = os.path.relpath(yml_file, os.getcwd())
            console.print(f"\n{file_path}", style="bold yellow")
            for lineno, prop, m in matches:
                # Highlight the matching part in the property value
                lower_m = m.lower()
                start = lower_m.find(term)
                if start != -1:
                    end = start + len(term)
                    text = Text(m)
                    text.stylize("bold red", start, end)
                else:
                    text = Text(m)
                if getattr(ns, "lines", False):
                    console.print(f"- Line {lineno}, {prop}: ", end="")
                    console.print(text)
                else:
                    console.print(f"- [blue]{prop}[/blue]: ", end="")
                    console.print(text)
    if not found_any:
        console.print(f"No matches found for: {ns.term}", style="red")
    return 0


@dataclass
class _Command:
    name: str = "search"
    help: str = "Search the knowledge base"
    build_parser = staticmethod(build_parser)
    run = staticmethod(run)


COMMAND = _Command()

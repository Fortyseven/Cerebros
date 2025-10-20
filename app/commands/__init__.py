"""Command submodule.

Each command lives in its own module inside this package and exposes a
``COMMAND`` object implementing the minimal interface required by the CLI
loader.

Interface (protocol style):
    name: str                  # command name used on CLI
    help: str                  # short help sentence
    build_parser(prog: str) -> argparse.ArgumentParser
    run(ctx: CommandContext, ns: argparse.Namespace) -> int

The ``load_commands`` function imports all modules in this directory (excluding
private/dunder and non-.py files) and collects their COMMAND objects.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import pkgutil
import argparse
from typing import Dict, Iterable

# Note: Command modules import CommandContext directly from app.cli; we avoid
# importing it here to prevent circular imports when the main script loads.


@dataclass
class LoadedCommand:
    name: str
    help: str
    build_parser: callable
    run: callable


def iter_command_module_names() -> Iterable[str]:
    package = __name__
    for mod in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
        if mod.ispkg:
            continue
        name = mod.name
        if name.startswith("_"):
            continue
        yield name


def load_commands() -> Dict[str, LoadedCommand]:
    commands: Dict[str, LoadedCommand] = {}
    for module_name in iter_command_module_names():
        full_name = f"{__name__}.{module_name}"
        module = importlib.import_module(full_name)
        if not hasattr(module, "COMMAND"):
            continue
        cmd = module.COMMAND
        # Basic validation
        if not all(
            hasattr(cmd, attr) for attr in ("name", "help", "build_parser", "run")
        ):
            continue
        commands[cmd.name] = LoadedCommand(
            name=cmd.name,
            help=cmd.help,
            build_parser=cmd.build_parser,
            run=cmd.run,
        )
    return commands


__all__ = ["load_commands", "LoadedCommand"]

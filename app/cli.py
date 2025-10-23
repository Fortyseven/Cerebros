"""Shared CLI types and helpers."""

from __future__ import annotations

from dataclasses import dataclass


from rich.console import Console


@dataclass
class CommandContext:
    """Global options passed to command handlers."""

    verbose: int = 0
    workspace: str = None
    no_color: bool = False
    console: Console = None


__all__ = ["CommandContext"]

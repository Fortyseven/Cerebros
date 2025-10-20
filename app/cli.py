"""Shared CLI types and helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CommandContext:
    """Global options passed to command handlers."""

    verbose: int = 0
    workspace: str = None


__all__ = ["CommandContext"]

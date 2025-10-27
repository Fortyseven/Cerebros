"""Formatting helpers for YAML content display in the browse TUI."""

from __future__ import annotations

from typing import Any, Optional


def _highlight(value: str, term: Optional[str]) -> str:
    if not term:
        return value
    lower_val = value.lower()
    lower_term = term.lower()
    start = 0
    pieces = []
    while True:
        idx = lower_val.find(lower_term, start)
        if idx == -1:
            pieces.append(value[start:])
            break
        pieces.append(value[start:idx])
        match_segment = value[idx : idx + len(term)]
        pieces.append(f"[bold red]{match_segment}[/bold red]")
        start = idx + len(term)
    return "".join(pieces)


def format_yaml_object(
    obj: Any, indent: int = 0, search_term: Optional[str] = None
) -> str:
    """Return a rich-markup formatted representation of a YAML-loaded object.

    The output is intended for direct consumption by a Textual Static widget.
    """
    pad = "  " * indent
    if isinstance(obj, dict):
        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}[bold blue]{k}[/bold blue]:")
                lines.append(format_yaml_object(v, indent + 1))
            else:
                v_str = _highlight(str(v), search_term)
                lines.append(f"{pad}[blue]{k}[/blue]: [green]{v_str}[/green]")
        return "\n".join(lines) if lines else f"{pad}[dim]<empty dict>[/dim]"
    if isinstance(obj, list):
        if not obj:
            return f"{pad}[dim]<empty list>[/dim]"
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(format_yaml_object(item, indent + 1))
            else:
                item_str = _highlight(str(item), search_term)
                lines.append(f"{pad}- [green]{item_str}[/green]")
        return "\n".join(lines)
    return f"{pad}[green]{_highlight(str(obj), search_term)}[/green]"


__all__ = ["format_yaml_object"]

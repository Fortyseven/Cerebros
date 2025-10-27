"""Browse command module.

Provides an interactive TUI (Textual) to explore the workspace and view YAML
entity files. Left pane: directory tree. Right pane: formatted YAML content.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import yaml
from typing import Any

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
    # Lazy import textual so regular commands don't require it.
    try:
        from textual.app import App, ComposeResult
        from textual.widgets import Tree, Static
        from textual.containers import Horizontal
        from textual.reactive import reactive
    except ImportError:
        ctx.console.print(
            "[red]textual library not installed. Please install with 'pip install textual'.[/red]"
        )
        return 1

    root_dir = ns.root or ctx.workspace
    if not root_dir or not os.path.isdir(root_dir):
        ctx.console.print(f"[red]Invalid root directory: {root_dir!r}[/red]")
        return 1

    class YamlViewer(Static):
        """Widget to display formatted YAML content."""

        file_path: reactive[str | None] = reactive(None)

        def watch_file_path(self, path: str | None) -> None:  # type: ignore[override]
            if path is None:
                self.update("[dim]Select a YAML file from the tree.[/dim]")
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except Exception as e:
                self.update(f"[red]Failed to read {path}: {e}[/red]")
                return
            formatted = format_yaml_object(data)
            self.update(formatted)

    def format_yaml_object(obj: Any, indent: int = 0) -> str:
        """Return a rich-markup formatted representation of a YAML-loaded object."""
        pad = "  " * indent
        if isinstance(obj, dict):
            lines = []
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}[bold blue]{k}[/bold blue]:")
                    lines.append(format_yaml_object(v, indent + 1))
                else:
                    lines.append(f"{pad}[blue]{k}[/blue]: [green]{v}[/green]")
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
                    lines.append(f"{pad}- [green]{item}[/green]")
            return "\n".join(lines)
        return f"{pad}[green]{obj}[/green]"

    def build_tree(tree: Tree, start_path: str) -> None:
        """Populate a Textual Tree with directory structure starting at start_path."""

        def add_dir(node, path):
            try:
                entries = sorted(os.listdir(path))
            except Exception:
                return
            for entry in entries:
                full = os.path.join(path, entry)
                label = entry
                if os.path.isdir(full):
                    child = node.add(
                        label, expand=False, data={"path": full, "is_dir": True}
                    )
                    # Pre-populate with a placeholder so it can be expanded lazily
                    child.add("...", data={"placeholder": True})
                else:
                    node.add(label, data={"path": full, "is_dir": False})

        root_node = tree.root
        root_node.data = {"path": start_path, "is_dir": True}
        add_dir(root_node, start_path)

    class BrowseApp(App):
        CSS = """
        Screen { layout: horizontal; }
        Tree { width: 40%; border: solid gray; }
        .content { border: solid gray; }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("r", "refresh", "Refresh"),
        ]

        def compose(self) -> ComposeResult:  # type: ignore[override]
            with Horizontal():
                tree = Tree(root_dir, id="dir-tree")
                viewer = YamlViewer(id="viewer", classes="content")
                yield tree
                yield viewer

        def on_mount(self) -> None:  # type: ignore[override]
            tree = self.query_one("#dir-tree", Tree)
            build_tree(tree, root_dir)

        def action_refresh(self) -> None:
            tree = self.query_one("#dir-tree", Tree)
            tree.root.clear()
            build_tree(tree, root_dir)
            viewer = self.query_one("#viewer", YamlViewer)
            viewer.file_path = None

        def on_tree_node_expanded(self, event: Tree.NodeSelected) -> None:  # type: ignore[override]
            node = event.node
            data = getattr(node, "data", {}) or {}
            path = data.get("path")
            is_dir = data.get("is_dir")
            if not path or not is_dir:
                return
            # Remove placeholder children
            for child in list(node.children):
                child_data = getattr(child, "data", {}) or {}
                if child_data.get("placeholder"):
                    child.remove()
            # Populate if empty
            if not list(node.children):
                try:
                    entries = sorted(os.listdir(path))
                except Exception:
                    return
                for entry in entries:
                    full = os.path.join(path, entry)
                    if os.path.isdir(full):
                        child = node.add(
                            entry, expand=False, data={"path": full, "is_dir": True}
                        )
                        child.add("...", data={"placeholder": True})
                    else:
                        node.add(entry, data={"path": full, "is_dir": False})

        def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:  # type: ignore[override]
            node = event.node
            data = getattr(node, "data", {}) or {}
            path = data.get("path")
            is_dir = data.get("is_dir")
            if not path or is_dir:
                return
            if path.endswith(".yml"):
                viewer = self.query_one("#viewer", YamlViewer)
                viewer.file_path = path
            else:
                viewer = self.query_one("#viewer", YamlViewer)
                viewer.file_path = None

    app = BrowseApp()
    app.run()
    return 0


@dataclass
class _Command:
    name: str = "browse"
    help: str = "Browse workspace in an interactive TUI"
    build_parser = staticmethod(build_parser)
    run = staticmethod(run)


COMMAND = _Command()

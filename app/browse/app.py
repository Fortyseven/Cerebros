"""Textual application definition for the browse TUI."""

from __future__ import annotations

import os
import yaml
from textual.app import App, ComposeResult
from textual.widgets import Tree, Static, Input
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive

from .formatting import format_yaml_object
from .tree import build_tree, build_filtered_tree, expand_all


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
        except Exception as e:  # pragma: no cover - runtime IO
            self.update(f"[red]Failed to read {path}: {e}[/red]")
            return
        formatted = format_yaml_object(data, search_term=self.app.search_term)  # type: ignore[attr-defined]
        self.update(formatted)


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

    def __init__(self, root_dir: str):
        super().__init__()
        self.root_dir = root_dir
        self.search_term: str | None = None
        self.matched_files: list[str] = []

    def compose(self) -> ComposeResult:  # type: ignore[override]
        with Vertical():
            # Search input on top
            yield Input(placeholder="Search (press Enter)...", id="search-input")
            with Horizontal():
                tree = Tree(self.root_dir, id="dir-tree")
                viewer = YamlViewer(id="viewer", classes="content")
                yield tree
                yield viewer

    def on_mount(self) -> None:  # type: ignore[override]
        tree = self.query_one("#dir-tree", Tree)
        build_tree(tree, self.root_dir)
        self.query_one("#search-input", Input).focus()

    def action_refresh(self) -> None:
        self.search_term = None
        self.matched_files = []
        tree = self.query_one("#dir-tree", Tree)
        self._rebuild_tree(tree)
        viewer = self.query_one("#viewer", YamlViewer)
        viewer.file_path = None
        search = self.query_one("#search-input", Input)
        search.value = ""

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
            except Exception:  # pragma: no cover - runtime IO
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
        viewer = self.query_one("#viewer", YamlViewer)
        if path.endswith(".yml"):
            viewer.file_path = path
        else:
            viewer.file_path = None

    def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[override]
        term = event.value.strip()
        self.search_term = term or None
        tree = self.query_one("#dir-tree", Tree)
        self._rebuild_tree(tree)
        viewer = self.query_one("#viewer", YamlViewer)
        viewer.file_path = None

    def _scan_for_term(self, term: str):
        term_lower = term.lower()
        for root, _, files in os.walk(self.root_dir):
            for f in files:
                if not f.endswith(".yml"):
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        text = fh.read().lower()
                except Exception:
                    continue
                if term_lower in text:
                    yield path

    def _rebuild_tree(self, tree: Tree) -> None:
        # Clear current children
        for child in list(tree.root.children):
            child.remove()
        if self.search_term:
            self.matched_files = list(self._scan_for_term(self.search_term))
            build_filtered_tree(tree, self.root_dir, self.matched_files)
            expand_all(tree)
        else:
            self.matched_files = []
            build_tree(tree, self.root_dir)

    def on_input_changed(self, event: Input.Changed) -> None:  # type: ignore[override]
        term = event.value.strip()
        self.search_term = term or None
        tree = self.query_one("#dir-tree", Tree)
        self._rebuild_tree(tree)


def run_browse_app(root_dir: str) -> None:
    app = BrowseApp(root_dir)
    app.run()


__all__ = ["BrowseApp", "run_browse_app"]

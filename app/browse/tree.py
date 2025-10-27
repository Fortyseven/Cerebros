"""Directory tree building utilities for the browse TUI."""

from __future__ import annotations

import os
from textual.widgets import Tree
from typing import Iterable


def build_tree(tree: Tree, start_path: str) -> None:
    """Populate a Textual Tree with directory structure starting at start_path."""

    def add_dir(node, path):
        try:
            entries = sorted(os.listdir(path))
        except Exception:  # pragma: no cover - filesystem errors
            return
        for entry in entries:
            full = os.path.join(path, entry)
            label = entry
            if os.path.isdir(full):
                child = node.add(
                    label, expand=False, data={"path": full, "is_dir": True}
                )
                child.add("...", data={"placeholder": True})
            else:
                node.add(label, data={"path": full, "is_dir": False})

    root_node = tree.root
    root_node.data = {"path": start_path, "is_dir": True}
    add_dir(root_node, start_path)


__all__ = ["build_tree"]


def build_filtered_tree(
    tree: Tree, start_path: str, matched_files: Iterable[str]
) -> None:
    """Populate tree only with directories leading to matched_files and those files.

    matched_files should be absolute paths. We create intermediate directory nodes
    as needed. Non-matching files are omitted.
    """
    start_path = os.path.abspath(start_path)
    matched_set = {os.path.abspath(p) for p in matched_files}
    root = tree.root
    root.data = {"path": start_path, "is_dir": True}

    # Precompute directory chains
    dir_children = {}
    for file_path in matched_set:
        if not file_path.startswith(start_path):
            continue
        rel = os.path.relpath(file_path, start_path)
        parts = rel.split(os.sep)
        # Walk parts building directory structure
        cur_dir = start_path
        for part in parts[:-1]:
            next_dir = os.path.join(cur_dir, part)
            dir_children.setdefault(cur_dir, set()).add(next_dir)
            cur_dir = next_dir
        # Add file to its parent directory listing
        dir_children.setdefault(cur_dir, set()).add(file_path)

    node_map = {start_path: root}

    def ensure_node(path: str):
        if path in node_map:
            return node_map[path]
        parent = os.path.dirname(path)
        parent_node = ensure_node(parent)
        label = os.path.basename(path)
        new_node = parent_node.add(
            label, expand=False, data={"path": path, "is_dir": True}
        )
        node_map[path] = new_node
        return new_node

    # Create directory nodes
    for parent, children in dir_children.items():
        parent_node = ensure_node(parent)
        for child in sorted(children):
            if os.path.isdir(child):
                ensure_node(child)
            else:
                parent_node.add(
                    os.path.basename(child), data={"path": child, "is_dir": False}
                )


__all__.append("build_filtered_tree")


def expand_all(tree: Tree) -> None:
    """Expand all directory nodes in the tree (depth-first)."""

    def _expand(node):
        data = getattr(node, "data", {}) or {}
        if data.get("is_dir"):
            node.expand()
            for child in node.children:
                _expand(child)

    _expand(tree.root)


__all__.append("expand_all")

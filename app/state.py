# Shared state for Cerebros CLI
# This module holds the workspace path, set by cerebros.py and used by subcommands.

from typing import Optional

workspace: Optional[str] = None

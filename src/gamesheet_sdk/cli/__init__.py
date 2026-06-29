# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Command-line interface for gamesheet_sdk.

The CLI is organized into a package with:

- **core.py** — ResourceGroup class, decorators, and utility functions
- **helpers.py** — Shared helper functions for commands
- **commands/** — Individual command modules
- **main.py** — Main CLI entry point

The public API exports only what's needed by tests and the entry point.
"""

from __future__ import annotations

from gamesheet_sdk.cli.core import (
    ResourceGroup,
    confirm_destructive,
    parse_columns_spec,
)
from gamesheet_sdk.cli.main import cli, main

__all__ = [
    "ResourceGroup",
    "cli",
    "confirm_destructive",
    "main",
    "parse_columns_spec",
]

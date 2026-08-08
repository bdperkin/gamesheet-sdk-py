#!/usr/bin/env python3
# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Check if API documentation is up-to-date with source code.

This script compares the modification times of source files against generated API documentation to detect when
docs need regeneration.
"""

from __future__ import annotations

import sys

# pylint: disable-next=import-error
from _constants import (
    AUTOSUMMARY_DIR,
    PACKAGE_DIR,
)
from rich import print as rprint

# Alias for backward compatibility
SRC_DIR = PACKAGE_DIR


def get_newest_source_mtime() -> float:
    """Get the modification time of the newest source file.

    Returns:
        float: Return value.
    """
    if not SRC_DIR.exists():
        return 0.0
    source_files = list(SRC_DIR.rglob("*.py"))
    if not source_files:
        return 0.0
    return float(max(f.stat().st_mtime for f in source_files))


def get_oldest_doc_mtime() -> float:
    """Get the modification time of the oldest generated doc file.

    Returns:
        float: Return value.
    """
    if not AUTOSUMMARY_DIR.exists():
        return 0.0
    doc_files = list(AUTOSUMMARY_DIR.glob("*.rst"))
    if not doc_files:
        return 0.0
    return float(min(f.stat().st_mtime for f in doc_files))


def main() -> int:
    """Check if API docs need regeneration.

    Returns:
        int: Integer exit code.
    """
    newest_source = get_newest_source_mtime()
    oldest_doc = get_oldest_doc_mtime()
    if not newest_source:
        rprint("[bold red]ERROR:[/bold red] No source files found")
        return 1
    if not oldest_doc:
        rprint(
            "[bold yellow]WARNING:[/bold yellow] No API documentation "
            "found. Run: [cyan]python docs/generate_api_docs.py[/cyan]",
        )
        return 1
    if newest_source > oldest_doc:
        rprint(
            "[bold yellow]WARNING:[/bold yellow] Source files are newer than API documentation. "
            "Run: [cyan]python docs/generate_api_docs.py[/cyan]",
        )
        return 1
    rprint("[bold green]✓[/bold green] API documentation is up-to-date")
    return 0


if __name__ == "__main__":
    sys.exit(main())

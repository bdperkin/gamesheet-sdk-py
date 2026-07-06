# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared constants for documentation build scripts."""

from __future__ import annotations

from pathlib import Path

# Paths relative to the docs directory
DOCS_DIR = Path(__file__).parent
PROJECT_ROOT = DOCS_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
PACKAGE_DIR = SRC_DIR / "gamesheet_sdk"

# Sphinx-generated API documentation directory
AUTOSUMMARY_DIR = DOCS_DIR / "reference" / "_autosummary"

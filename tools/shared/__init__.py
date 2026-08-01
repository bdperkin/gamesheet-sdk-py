# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared utilities for CLI tools."""

from __future__ import annotations

from pathlib import Path

from shared.toml import load_toml

_PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"

PROJECT_NAME: str = load_toml(_PYPROJECT_PATH)["project"]["name"]

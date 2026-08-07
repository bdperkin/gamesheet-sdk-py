# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared TOML file loading for CLI tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.exceptions import ToolError
import tomli


def load_toml(path: Path) -> dict[str, Any]:
    """Read and parse a TOML file.

    Args:
        path (Path): Path-like object to the TOML file.

    Returns:
        dict[str, Any]: Parsed TOML data as a dict.

    Raises:
        ToolError: If the file cannot be read or contains invalid TOML.
    """
    try:
        with path.open("rb") as f:
            return tomli.load(f)
    except OSError as exc:
        msg = f"Cannot read {path}: {exc}"
        raise ToolError(msg) from exc
    except tomli.TOMLDecodeError as exc:
        msg = f"Invalid TOML in {path}: {exc}"
        raise ToolError(msg) from exc


_PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"

PROJECT_NAME: str = load_toml(_PYPROJECT_PATH)["project"]["name"]

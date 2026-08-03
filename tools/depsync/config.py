# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Static defaults and constants for dependency convergence."""

from __future__ import annotations

PYPROJECT_TOML = "pyproject.toml"

PRECOMMIT_CONFIG = ".pre-commit-config.yaml"

GENPRECOMMIT_CONFIG = ".genprecommitconfig.yaml"

UV_LOCK = "uv.lock"

PYPI_API_URL = "https://pypi.org/pypi/{package}/json"

PYPI_TIMEOUT = 10

UV_LOCK_TIMEOUT = 120

TOOL_MAPPING: dict[str, str] = {
    "mypy": "https://github.com/pre-commit/mirrors-mypy",
    "pre-commit-uv": "https://github.com/astral-sh/uv-pre-commit",
    "pymarkdownlnt": "https://github.com/jackdewinter/pymarkdown",
    "ruff": "https://github.com/astral-sh/ruff-pre-commit",
    "semgrep": "https://github.com/semgrep/pre-commit",
    "shfmt-py": "https://github.com/scop/pre-commit-shfmt",
}

REVERSE_MAPPING: dict[str, str] = {url: pkg for pkg, url in TOOL_MAPPING.items()}

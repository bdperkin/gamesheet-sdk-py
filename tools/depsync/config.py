# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Static defaults and constants for dependency convergence."""

from __future__ import annotations

PYPROJECT_TOML = "pyproject.toml"

PRECOMMIT_CONFIG = ".pre-commit-config.yaml"

GENPRECOMMIT_CONFIG = ".genprecommitconfig.yaml"

DEPENDABOT_CONFIG = ".github/dependabot.yml"

OVERRIDES_CONFIG = ".syncdepsoverrides.yaml"

UV_LOCK = "uv.lock"

PYPI_API_URL = "https://pypi.org/pypi/{package}/json"

PYPI_TIMEOUT = 10

UV_LOCK_TIMEOUT = 120

TOOL_MAPPING: dict[str, str] = {
    "editorconfig-checker": "https://github.com/editorconfig-checker/editorconfig-checker.python",
    "mypy": "https://github.com/pre-commit/mirrors-mypy",
    "pymarkdownlnt": "https://github.com/jackdewinter/pymarkdown",
    "pyrefly": "https://github.com/facebook/pyrefly-pre-commit",
    "pyright": "https://github.com/robertcraigie/pyright-python",
    "ruff": "https://github.com/astral-sh/ruff-pre-commit",
    "semgrep": "https://github.com/semgrep/pre-commit",
}

REVERSE_MAPPING: dict[str, str] = {url: pkg for pkg, url in TOOL_MAPPING.items()}


def repo_url_to_package(url: str) -> str | None:
    """Map a pre-commit repo URL to its PyPI package name.

    Consults ``REVERSE_MAPPING`` first for repos whose name differs from the package they ship (mirrors,
    ``*-pre-commit`` wrappers), then falls back to the URL basename.

    Args:
        url (str): Repository URL.

    Returns:
        str | None: Package name, or None if the URL has no usable basename.
    """
    if url in REVERSE_MAPPING:
        return REVERSE_MAPPING[url]

    last_segment = url.rstrip("/").rsplit("/", maxsplit=1)[-1]
    return last_segment.lower() if last_segment else None

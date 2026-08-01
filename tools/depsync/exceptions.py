# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Dependency convergence exception hierarchy."""

from __future__ import annotations

from shared.exceptions import ToolError


class SyncDepsError(ToolError):
    """Base error for dependency convergence."""


class ParseError(SyncDepsError):
    """Configuration file parsing failed."""


class FetchError(SyncDepsError):
    """PyPI or git tag fetch failed."""


class WriteError(SyncDepsError):
    """File write failed."""


class LockfileError(SyncDepsError):
    """uv.lock generation or validation failed."""

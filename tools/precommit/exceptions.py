# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Pre-commit configuration generation exception hierarchy."""

from __future__ import annotations

from shared.exceptions import SubprocessError as _SubprocessError, ToolError


class GenPreCommitConfigError(ToolError):
    """Base error for pre-commit configuration generation."""


class ConfigError(GenPreCommitConfigError):
    """Configuration file loading or validation failed."""


class DiscoveryError(GenPreCommitConfigError):
    """Git tag resolution or version discovery failed."""


class FetchError(GenPreCommitConfigError):
    """Remote hook definition fetch failed."""


class ProcessingError(GenPreCommitConfigError):
    """Hook filtering or modification failed."""


class RenderError(GenPreCommitConfigError):
    """YAML output generation failed."""


class PreCommitValidationError(GenPreCommitConfigError):
    """Pre-commit validation run failed."""


class SubprocessError(GenPreCommitConfigError, _SubprocessError):
    """Subprocess command failed."""

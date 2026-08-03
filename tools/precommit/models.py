# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Pydantic v2 models for pre-commit configuration generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from precommit.config import (
    DEFAULT_ALLOWED_LANGUAGES,
    DEFAULT_FAIL_FAST,
    DEFAULT_LANGUAGE_VERSION,
    DEFAULT_MAX_DOWNGRADE_ATTEMPTS,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_STAGES,
)
from pydantic import BaseModel, Field


class HookConfig(BaseModel):
    """Per-hook override/append configuration from the config file."""

    id: str = Field(description="Hook identifier to match against fetched hooks")
    comment: str | None = Field(
        default=None,
        description="Rendered as a YAML comment above the hook",
    )
    overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Fields that replace fetched hook values entirely",
    )
    appends: dict[str, list[Any]] = Field(
        default_factory=dict,
        description="Fields whose values are appended to fetched hook lists",
    )
    prepends: dict[str, list[Any]] = Field(
        default_factory=dict,
        description="Fields whose values are prepended to fetched hook lists",
    )


class RepoConfig(BaseModel):
    """Repository entry from the config file."""

    name: str = Field(description="Common/friendly name for the repository")
    repo: str = Field(description="Repository URL or 'meta'")
    rev: str | None = Field(
        default=None,
        description="Pinned revision, 'installed' for package version, or None for latest tag",
    )
    resolved_rev: str | None = Field(
        default=None,
        description="Tool-resolved revision written by genprecommitconfig on downgrade",
    )
    hooks: list[HookConfig] = Field(
        default_factory=list,
        description="Per-hook override and append configurations",
    )


class CategoryConfig(BaseModel):
    """Category grouping with a description and list of repos."""

    description: str = Field(
        description="Human-readable label rendered as a sub-section comment",
    )
    repos: list[RepoConfig] = Field(
        default_factory=list,
        description="Repositories in this category",
    )


class GlobalConfig(BaseModel):
    """Global settings from the config file."""

    default_language_version: dict[str, str] = Field(
        default_factory=DEFAULT_LANGUAGE_VERSION.copy,
    )
    default_stages: list[str] = Field(
        default_factory=DEFAULT_STAGES.copy,
    )
    fail_fast: bool = DEFAULT_FAIL_FAST
    files: str | None = Field(
        default=None,
        description="Global regex for files to include",
    )
    exclude: str | None = Field(
        default=None,
        description="Global regex for files to exclude",
    )
    minimum_pre_commit_version: str | None = Field(
        default=None,
        description="Minimum pre-commit version required",
    )
    output_file: str = DEFAULT_OUTPUT_FILE
    allowed_languages: list[str] = Field(
        default_factory=DEFAULT_ALLOWED_LANGUAGES.copy,
    )
    blacklisted_hooks: list[str] = Field(default_factory=list)
    max_downgrade_attempts: int = DEFAULT_MAX_DOWNGRADE_ATTEMPTS


class ToolConfig(BaseModel):
    """Root configuration model validated from the YAML config file."""

    model_config = {"populate_by_name": True}

    global_config: GlobalConfig = Field(default_factory=GlobalConfig, alias="globals")
    ci: dict[str, Any] | None = Field(
        default=None,
        description="Pre-commit.ci service configuration, passed through as-is",
    )
    categories: dict[str, CategoryConfig] = Field(
        default_factory=dict,
        description="Repositories grouped by function (meta, check, lint, format, quality, misc)",
    )


class RunConfig(BaseModel):
    """CLI runtime configuration combining command-line args and parsed config."""

    config_file: Path
    output_file: Path | None = None
    log_level: str = Field(default="info", pattern=r"^(debug|info|warning|error)$")
    dry_run: bool = False
    validate_incremental: bool = True
    max_downgrade_attempts: int | None = None
    reset_on_failure: bool = True

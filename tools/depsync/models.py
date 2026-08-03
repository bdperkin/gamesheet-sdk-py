# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Pydantic v2 models for dependency convergence."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class UpdateTarget(StrEnum):
    """Which file(s) a convergence result targets."""

    PYPROJECT = "pyproject"
    GENPRECOMMIT = "genprecommit"
    BOTH = "both"


class PyProjectDependency(BaseModel):
    """A dependency extracted from pyproject.toml."""

    name: str = Field(description="Normalized package name")
    version: str | None = Field(
        default=None,
        description="Pinned version or None if unpinned",
    )
    extras: str | None = Field(
        default=None,
        description="Extras specifier like [tomli]",
    )
    original: str = Field(description="Original dependency string as written")
    group: str = Field(description="Optional-dependency group name or 'base'")


class PreCommitAdditionalDep(BaseModel):
    """An additional_dependency from a pre-commit hook."""

    name: str = Field(description="Normalized package name")
    version: str | None = Field(default=None, description="Pinned version or None")
    original: str = Field(description="Original dependency string")
    hook_id: str = Field(description="Hook ID this dependency belongs to")


class PreCommitRepo(BaseModel):
    """A repository entry from .pre-commit-config.yaml."""

    url: str = Field(description="Repository URL")
    rev: str = Field(description="Current revision/tag")
    hook_ids: list[str] = Field(
        default_factory=list,
        description="Hook IDs in this repo",
    )
    additional_deps: list[PreCommitAdditionalDep] = Field(
        default_factory=list,
        description="Non-local additional_dependencies across all hooks",
    )


class ConvergenceResult(BaseModel):
    """A single dependency update determined by the convergence engine."""

    package: str = Field(description="Package or repo name")
    old_version: str | None = Field(description="Current version")
    new_version: str = Field(description="Resolved target version")
    target: UpdateTarget = Field(description="Which file(s) to update")
    repo_url: str | None = Field(default=None, description="Git repo URL if applicable")
    groups: list[str] = Field(
        default_factory=list,
        description="pyproject.toml groups affected",
    )
    hook_ids: list[str] = Field(
        default_factory=list,
        description="Pre-commit hook IDs affected",
    )
    is_additional_dep: bool = Field(
        default=False,
        description="True if this is an additional_dependency",
    )
    is_pinned: bool = Field(
        default=False,
        description="True if rev is pinned in .genprecommitconfig.yaml",
    )
    needs_regeneration: bool = Field(
        default=False,
        description="True if .pre-commit-config.yaml rev is stale",
    )
    rev_tag: str | None = Field(
        default=None,
        description="Original git tag to write as rev",
    )


class TypesSyncResult(BaseModel):
    """Result of types-* stub synchronization."""

    added: list[tuple[str, str]] = Field(
        default_factory=list,
        description="(package_name, version) pairs for new stubs",
    )
    removed: list[str] = Field(
        default_factory=list,
        description="Package names of orphaned stubs removed",
    )
    updated: list[tuple[str, str, str]] = Field(
        default_factory=list,
        description="(package_name, old_version, new_version) for version bumps",
    )


class RunConfig(BaseModel):
    """CLI runtime configuration."""

    pyproject_path: Path = Field(default=Path("pyproject.toml"))
    precommit_config_path: Path = Field(default=Path(".pre-commit-config.yaml"))
    genprecommit_config_path: Path = Field(default=Path(".genprecommitconfig.yaml"))
    uv_lock_path: Path = Field(default=Path("uv.lock"))
    log_level: str = Field(default="info", pattern=r"^(debug|info|warning|error)$")
    dry_run: bool = False
    sync_types: bool = False
    backup: bool = False
    check: bool = False
    diff: bool = False

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Pydantic v2 models for dependency convergence."""

from __future__ import annotations

from datetime import date
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


class OverridePolicy(BaseModel):
    """One transitive-dependency override declared in ``.syncdepsoverrides.yaml``.

    Carries the *policy* — why the override exists and what versions are acceptable — as distinct from the
    resolved exact pin, which lives in ``pyproject.toml``.
    """

    package: str = Field(description="PyPI name of the transitive package to override")
    pinned_by: str = Field(description="Dependency whose requirement is being overridden")
    floor: str = Field(description="Lowest acceptable version as a PEP 440 specifier")
    ceiling: str | None = Field(
        default=None,
        description="Upper bound as a PEP 440 specifier, or None to float",
    )
    reason: str = Field(description="Why the override exists and why the bounds are what they are")
    verify: str | None = Field(
        default=None,
        description="Shell command that must exit 0 with the override applied",
    )
    review: date = Field(description="ISO date for the next review")

    def specifier(self) -> str:
        """Render the bounds as a single PEP 440 requirement for uv to resolve within.

        Returns:
            str: Requirement string such as ``mcp>=1.28.1,<2``.
        """
        bounds = self.floor if self.ceiling is None else f"{self.floor},{self.ceiling}"
        return f"{self.package}{bounds}"


class OverrideResult(BaseModel):
    """Outcome of converging one override policy."""

    package: str = Field(description="Package the override applies to")
    old_version: str | None = Field(description="Version currently pinned, or None if not yet overridden")
    new_version: str = Field(description="Version resolved within the declared bounds")
    retirable: bool = Field(
        default=False,
        description="True if a resolution without the override already satisfies the floor",
    )
    unpinned_version: str | None = Field(
        default=None,
        description="Version resolved without the override, for reporting retirement",
    )


class RunConfig(BaseModel):
    """CLI runtime configuration."""

    pyproject_path: Path = Field(default=Path("pyproject.toml"))
    precommit_config_path: Path = Field(default=Path(".pre-commit-config.yaml"))
    genprecommit_config_path: Path = Field(default=Path(".genprecommitconfig.yaml"))
    dependabot_path: Path = Field(default=Path(".github/dependabot.yml"))
    overrides_path: Path = Field(default=Path(".syncdepsoverrides.yaml"))
    uv_lock_path: Path = Field(default=Path("uv.lock"))
    log_level: str = Field(default="info", pattern=r"^(debug|info|warning|error)$")
    dry_run: bool = False
    sync_types: bool = False
    no_uv_resolve: bool = False
    backup: bool = False
    check: bool = False
    diff: bool = False

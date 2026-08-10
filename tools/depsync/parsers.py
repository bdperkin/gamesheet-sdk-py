# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Parsers for pyproject.toml and .pre-commit-config.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any

from depsync.exceptions import ParseError
from depsync.models import PreCommitAdditionalDep, PreCommitRepo, PyProjectDependency
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version
from ruamel.yaml import YAML
from shared import PROJECT_NAME
from shared.exceptions import ToolError
from shared.toml import load_toml

logger = logging.getLogger(__name__)


def _is_local_dependency(dep_string: str) -> bool:
    return dep_string.strip("'\" ").startswith((".", "/"))


def _is_url_dependency(dep_string: str) -> bool:
    return " @ " in dep_string or "git+" in dep_string


def _has_inequality_constraint(dep_string: str) -> bool:
    return (
        ">=" in dep_string
        or "<=" in dep_string
        or "~=" in dep_string
        or "!=" in dep_string
        or ">" in dep_string
        or "<" in dep_string
    )


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _is_self_reference(dep_string: str) -> bool:
    """Check whether a dependency string refers to this project itself.

    Self-references like ``gamesheet-sdk-py[mypy,tools]`` exist so a hook environment picks up the project's
    own extras. They carry no version to converge, and the writers refuse to touch them, so treating one as a
    convergeable package produces a phantom "update" that never lands — and, in ``--check`` mode, a permanent
    exit 1.

    Returns:
        bool: True if the string names this project.
    """
    name = dep_string.strip().split("==", maxsplit=1)[0].split("[", maxsplit=1)[0]
    return _normalize_name(name) == _normalize_name(PROJECT_NAME)


def _parse_dep_string(
    dep_raw: str,
    group: str,
) -> PyProjectDependency | None:
    dep = dep_raw.strip()
    if not dep or "@" in dep or "<" in dep or ">" in dep:
        return None

    if dep.startswith(f"{PROJECT_NAME}["):
        return None

    extras = None
    name_part = dep
    version = None

    if "==" in dep:
        name_part, version = dep.split("==", 1)

    match = re.match(r"^([a-zA-Z0-9\-_.]+)(\[.+?\])?$", name_part.strip())
    if not match:
        return None

    raw_name = match.group(1)
    extras = match.group(2)

    return PyProjectDependency(
        name=_normalize_name(raw_name),
        version=version,
        extras=extras,
        original=dep,
        group=group,
    )


def parse_pyproject(path: Path) -> dict[str, list[PyProjectDependency]]:
    """Parse dependencies from pyproject.toml.

    Args:
        path (Path): Path to pyproject.toml.

    Returns:
        dict[str, list[PyProjectDependency]]: Dict mapping normalized package names to lists of
            PyProjectDependency (one per group the package appears in).

    Raises:
        ParseError: If the file cannot be read or parsed.
    """
    try:
        data = load_toml(path)
    except ToolError as exc:
        raise ParseError(str(exc)) from exc

    deps: dict[str, list[PyProjectDependency]] = {}

    for dep_str in data.get("project", {}).get("dependencies", []):
        parsed = _parse_dep_string(dep_str, "base")
        if parsed:
            deps.setdefault(parsed.name, []).append(parsed)

    for group_name, group_deps in data.get("project", {}).get("optional-dependencies", {}).items():
        for dep_str in group_deps:
            parsed = _parse_dep_string(dep_str, group_name)
            if parsed:
                deps.setdefault(parsed.name, []).append(parsed)

    logger.debug("Parsed %d unique packages from %s", len(deps), path)
    return deps


def _parse_additional_dep(
    raw_dep_str: str,
    hook_id: str,
) -> PreCommitAdditionalDep | None:
    dep_str = raw_dep_str.strip()
    if not dep_str:
        return None

    if "==" in dep_str:
        parts = dep_str.split("==", 1)
        name_part = parts[0].strip()
        version = parts[1].strip()
        name_match = re.match(r"^([a-zA-Z0-9\-_]+)", name_part)
        if name_match:
            return PreCommitAdditionalDep(
                name=_normalize_name(name_match.group(1)),
                version=version,
                original=dep_str,
                hook_id=hook_id,
            )

        return None

    name_match = re.match(r"^([a-zA-Z0-9\-_]+)", dep_str)
    if name_match:
        return PreCommitAdditionalDep(
            name=_normalize_name(name_match.group(1)),
            version=None,
            original=dep_str,
            hook_id=hook_id,
        )

    return None


def _parse_repo_hooks(
    repo_entry: dict[str, Any],
) -> tuple[list[str], list[PreCommitAdditionalDep]]:
    """Process hooks from a single repo entry.

    Args:
        repo_entry (dict[str, Any]): A single repo mapping from .pre-commit-config.yaml.

    Returns:
        tuple[list[str], list[PreCommitAdditionalDep]]: Tuple of (hook_ids, additional_deps) extracted from
            the repo's hooks.
    """
    hook_ids: list[str] = []
    additional_deps: list[PreCommitAdditionalDep] = []

    for hook in repo_entry.get("hooks", []):
        hook_id = hook.get("id", "")
        hook_ids.append(hook_id)
        for ad in hook.get("additional_dependencies", []):
            ad_str = str(ad)
            if (
                _is_local_dependency(ad_str)
                or _is_url_dependency(ad_str)
                or _has_inequality_constraint(ad_str)
                or _is_self_reference(ad_str)
            ):
                continue

            ad_parsed = _parse_additional_dep(ad_str, hook_id)
            if ad_parsed:
                additional_deps.append(ad_parsed)

    return hook_ids, additional_deps


def parse_precommit_config(path: Path) -> list[PreCommitRepo]:
    """Parse repositories from .pre-commit-config.yaml.

    Args:
        path (Path): Path to .pre-commit-config.yaml.

    Returns:
        list[PreCommitRepo]: List of PreCommitRepo entries (skipping 'meta' and 'local' repos).

    Raises:
        ParseError: If the file cannot be read or parsed.
    """
    yaml = YAML()
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.load(f)
    except Exception as exc:
        msg = f"Failed to parse {path}: {exc}"
        raise ParseError(msg) from exc

    repos: list[PreCommitRepo] = []
    if data is None:
        return repos

    for repo_entry in data.get("repos", []):
        url = repo_entry.get("repo", "")
        if url in {"meta", "local"} or not url.startswith("https://"):
            continue

        rev = str(repo_entry.get("rev", ""))
        hook_ids, additional_deps = _parse_repo_hooks(repo_entry)

        repos.append(
            PreCommitRepo(
                url=url,
                rev=rev,
                hook_ids=hook_ids,
                additional_deps=additional_deps,
            ),
        )

    logger.debug("Parsed %d repos from %s", len(repos), path)
    return repos


def _extract_pinned_from_data(data: dict[str, Any]) -> dict[str, str]:
    """Iterate category repos and build the pinned revs dict.

    Args:
        data (dict[str, Any]): Parsed YAML data from .genprecommitconfig.yaml.

    Returns:
        dict[str, str]: Dict mapping repo URL to pinned rev string.
    """
    pinned: dict[str, str] = {}
    for cat in (data.get("categories") or {}).values():
        if not cat:
            continue

        for repo_entry in cat.get("repos", []):
            url = repo_entry.get("repo", "")
            if not url.startswith("https://"):
                continue

            rev = repo_entry.get("rev")
            if rev is not None and str(rev) != "installed":
                pinned[url] = str(rev)
                continue

            resolved_rev = repo_entry.get("resolved_rev")
            if resolved_rev is not None:
                pinned[url] = str(resolved_rev)

    return pinned


def parse_genprecommit_pinned_revs(path: Path) -> dict[str, str]:
    """Extract pinned rev or resolved_rev values from .genprecommitconfig.yaml.

    Repos with an explicit ``rev:`` key take precedence. If ``rev`` is absent or ``installed``,
    ``resolved_rev`` is used as a fallback pin. Repos with neither are excluded.

    Args:
        path (Path): Path to .genprecommitconfig.yaml.

    Returns:
        dict[str, str]: Dict mapping repo URL to pinned rev string.

    Raises:
        ParseError: If the file cannot be read or parsed.
    """
    yaml = YAML()
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.load(f)
    except Exception as exc:
        msg = f"Failed to parse {path}: {exc}"
        raise ParseError(msg) from exc

    if data is None:
        return {}

    pinned = _extract_pinned_from_data(data)

    logger.debug("Found %d pinned revs in %s", len(pinned), path)
    return pinned


def parse_uv_lock(path: Path) -> tuple[set[str], set[str]]:
    """Parse all package names from uv.lock.

    Args:
        path (Path): Path to uv.lock.

    Returns:
        tuple[set[str], set[str]]: Tuple of (base_packages, all_packages) where base_packages excludes types-*
            entries and all_packages includes everything.

    Raises:
        ParseError: If the file cannot be read or parsed.
    """
    try:
        data = load_toml(path)
    except ToolError as exc:
        raise ParseError(str(exc)) from exc

    all_packages: set[str] = set()
    for pkg in data.get("package", []):
        name = pkg.get("name", "")
        if name:
            all_packages.add(_normalize_name(name))

    base_packages = {n for n in all_packages if not n.startswith("types-")}

    logger.debug(
        "Parsed %d packages from %s (%d base, %d types-*)",
        len(all_packages),
        path,
        len(base_packages),
        len(all_packages) - len(base_packages),
    )
    return base_packages, all_packages


def _parse_specifier_lower_bound(spec_str: str) -> Version | None:
    """Extract the lower-bound version from a PEP 440 specifier string.

    Returns:
        Version | None: The minimum Version from ``>=`` or ``~=``, or None on parse failure.
    """
    try:
        spec_set = SpecifierSet(spec_str)
    except InvalidSpecifier:
        logger.warning("Invalid requires-python specifier: %s", spec_str)
        return None

    for spec in spec_set:
        if spec.operator in {">=", "~="}:
            return Version(spec.version)

    return None


def parse_requires_python(path: Path) -> Version | None:
    """Extract the minimum Python version from ``requires-python`` in pyproject.toml.

    Parses the ``>=`` or ``~=`` lower bound from the specifier set.

    Args:
        path (Path): Path to pyproject.toml.

    Returns:
        Version | None: The minimum Python Version, or None if not configured.
    """
    try:
        data = load_toml(path)
    except ToolError:
        return None

    spec_str = data.get("project", {}).get("requires-python")
    if not spec_str:
        return None

    return _parse_specifier_lower_bound(spec_str)


def parse_index_url(path: Path) -> str | None:
    """Extract the package index URL from ``[tool.uv]`` in pyproject.toml.

    Args:
        path (Path): Path to pyproject.toml.

    Returns:
        str | None: The ``index-url`` string, or None if not configured.
    """
    try:
        data = load_toml(path)
    except ToolError:
        return None

    index_url = data.get("tool", {}).get("uv", {}).get("index-url")
    if isinstance(index_url, str) and index_url.strip():
        return index_url.strip()

    return None

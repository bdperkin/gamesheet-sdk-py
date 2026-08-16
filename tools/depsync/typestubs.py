# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Synchronization of ``types-*`` stub packages against the resolved dependency tree."""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

import requests
from shared import PROJECT_NAME
from shared.concurrency import PARALLEL_WORKERS
from shared.exceptions import ToolError
from shared.toml import load_toml

from depsync.engine import prefetch_versions
from depsync.exceptions import FetchError, ParseError
from depsync.fetchers import check_package_exists, resolve_latest_version
from depsync.models import TypesSyncResult
from depsync.typedness import collect_imported_modules, filter_stub_candidates, is_orphaned

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from packaging.version import Version
    from shared.pip_config import PipConfig

logger = logging.getLogger(__name__)


def _parse_type_stubs_types(pyproject_path: Path) -> dict[str, str | None]:
    """Extract types-* entries from the type-stubs optional-dependency group.

    Returns:
        dict[str, str | None]: Dict mapping normalized types-* package name to its pinned version (or None if
            unpinned).

    Raises:
        ParseError: If the file cannot be read or contains invalid TOML.

    """
    try:
        data = load_toml(pyproject_path)
    except ToolError as exc:
        raise ParseError(str(exc)) from exc

    type_stubs_deps = data.get("project", {}).get("optional-dependencies", {}).get("type-stubs", [])
    types_map: dict[str, str | None] = {}
    for dep_str in type_stubs_deps:
        dep = dep_str.strip()
        if not dep.lower().startswith("types-"):
            continue

        if "==" in dep:
            name_part, version = dep.split("==", 1)
        else:
            name_part, version = dep, None

        normalized = re.sub(r"[-_.]+", "-", name_part.strip()).lower()
        types_map[normalized] = version

    return types_map


def _discover_available_types(
    to_check: set[str],
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
) -> set[str]:
    """Check which candidate packages have types-* stubs available.

    Args:
        to_check (set[str]): Base package names to check.
        index_url (str | None): Optional PEP 503 index URL.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs to try.
        pip_config (PipConfig | None): Optional pip configuration for SSL settings.

    Returns:
        set[str]: Set of base package names whose types-* stub exists.

    """
    available: set[str] = set()

    def _check(name: str) -> tuple[str, bool]:
        types_name = f"types-{name}"
        return name, check_package_exists(
            types_name,
            index_url=index_url,
            extra_index_urls=extra_index_urls,
            pip_config=pip_config,
        )

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futures = {pool.submit(_check, name): name for name in to_check}
        for future in as_completed(futures):
            try:
                name, exists = future.result()
            except (FetchError, requests.RequestException):
                pkg = futures[future]
                logger.warning("Failed to check types-%s availability; skipping", pkg)
                continue

            if exists:
                available.add(name)
                logger.debug("  types-%s exists on index", name)

    return available


def _collect_types_to_fetch(
    available: set[str],
    current_types: dict[str, str | None],
    all_packages: set[str],
) -> set[str]:
    """Build the set of types-* package names whose versions need fetching.

    Returns:
        set[str]: Package names to fetch version data for.

    """
    types_to_fetch: set[str] = set()
    for name in available:
        types_name = f"types-{name}"
        if types_name not in current_types:
            types_to_fetch.add(types_name)

    for types_name in current_types:
        base_name = types_name.removeprefix("types-")
        if base_name in all_packages:
            types_to_fetch.add(types_name)

    return types_to_fetch


def _find_new_stubs(
    available: set[str],
    current_types: dict[str, str | None],
    types_cache: dict[str, dict[str, str | None]],
    min_python: Version | None,
) -> list[tuple[str, str]]:
    """Identify types-* stubs to add.

    Returns:
        list[tuple[str, str]]: List of (package_name, version) pairs.

    """
    added: list[tuple[str, str]] = []
    for name in sorted(available):
        types_name = f"types-{name}"
        if types_name not in current_types:
            latest = resolve_latest_version(types_cache.get(types_name, {}), min_python)
            if latest:
                added.append((types_name, latest))
                logger.info("  Add %s==%s", types_name, latest)

    return added


def _removal_reason(base_name: str, all_packages: set[str], imported: set[str]) -> str | None:
    """Explain why an existing stub no longer belongs, if it does not.

    A stub whose base package left the dependency tree is dead, and so is one whose module no file imports
    any more. Shipping ``py.typed`` is deliberately *not* grounds for removal — see
    :mod:`depsync.typedness`.

    Returns:
        str | None: Reason to remove the stub, or None to keep it.

    """
    if base_name not in all_packages:
        return "base package not in dependency tree"

    if is_orphaned(base_name, imported):
        return "no file imports the stubbed module any more"

    return None


def _find_stale_stubs(
    current_types: dict[str, str | None],
    all_packages: set[str],
    types_cache: dict[str, dict[str, str | None]],
    min_python: Version | None,
    imported: set[str],
) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Identify types-* stubs to remove or update.

    Returns:
        tuple[list[str], list[tuple[str, str, str]]]: Removed names and updated (name, old_version,
            new_version) triples.

    """
    removed: list[str] = []
    updated: list[tuple[str, str, str]] = []
    for types_name, current_version in sorted(current_types.items()):
        base_name = types_name.removeprefix("types-")
        reason = _removal_reason(base_name, all_packages, imported)
        if reason:
            removed.append(types_name)
            logger.info("  Remove %s (%s)", types_name, reason)
            continue

        latest = resolve_latest_version(types_cache.get(types_name, {}), min_python)
        if latest and latest != current_version:
            updated.append((types_name, current_version or "", latest))
            logger.info("  Update %s: %s → %s", types_name, current_version, latest)

    return removed, updated


def sync_types(
    base_packages: set[str],
    all_packages: set[str],
    pyproject_path: Path,
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
    min_python: Version | None = None,
    source_root: Path | None = None,
) -> TypesSyncResult:
    """Compute types-* stub additions, removals, and updates.

    Availability on the index is a necessary but not sufficient condition for an addition: a candidate must
    also pass the gates in :mod:`depsync.typedness` — the module has to be imported somewhere in the tree,
    and the runtime distribution must not already ship ``py.typed``. Gated-out candidates are reported in
    ``TypesSyncResult.skipped`` rather than dropped silently.

    Args:
        base_packages (set[str]): Non-types package names from uv.lock.
        all_packages (set[str]): All package names from uv.lock (including types-*).
        pyproject_path (Path): Path to pyproject.toml.
        index_url (str | None): Optional PEP 503 index URL.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs to try.
        pip_config (PipConfig | None): Optional pip configuration for SSL settings.
        min_python (Version | None): Minimum Python version to filter compatible releases.
        source_root (Path | None): Directory whose source tree is scanned for imports. Defaults to the
            directory holding *pyproject_path*.

    Returns:
        TypesSyncResult: TypesSyncResult describing all changes.

    """
    current_types = _parse_type_stubs_types(pyproject_path)
    imported = collect_imported_modules(source_root or pyproject_path.parent)

    candidates = {
        name for name in base_packages if not name.startswith(PROJECT_NAME) and name != "type-stubs"
    }

    already_known = {name.removeprefix("types-") for name in current_types}
    to_check, skipped = filter_stub_candidates(candidates - already_known, imported)

    logger.info(
        "Checking %d candidates for types-* stubs (%d already in type-stubs group, %d gated out)",
        len(to_check),
        len(already_known),
        len(skipped),
    )

    available = _discover_available_types(
        to_check,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
    )

    types_to_fetch = _collect_types_to_fetch(available, current_types, all_packages)
    types_cache, _ = prefetch_versions(
        types_to_fetch,
        set(),
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
    )

    result = TypesSyncResult()
    result.skipped = skipped
    result.added = _find_new_stubs(available, current_types, types_cache, min_python)
    result.removed, result.updated = _find_stale_stubs(
        current_types,
        all_packages,
        types_cache,
        min_python,
        imported,
    )

    return result

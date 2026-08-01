# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Core convergence algorithm for bidirectional dependency synchronization."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from pathlib import Path
import re

from depsync.config import REVERSE_MAPPING
from depsync.exceptions import FetchError, ParseError
from depsync.fetchers import (
    check_package_exists,
    clean_and_sort_versions,
    fetch_git_tags,
    fetch_pypi_versions,
    find_highest_common_version,
    resolve_latest_version,
)
from depsync.models import (
    ConvergenceResult,
    PreCommitRepo,
    PyProjectDependency,
    TypesSyncResult,
    UpdateTarget,
)
from packaging.version import InvalidVersion, Version
import requests
from shared import PROJECT_NAME
from shared.concurrency import PARALLEL_WORKERS
from shared.exceptions import ToolError
from shared.pip_config import PipConfig
from shared.toml import load_toml

logger = logging.getLogger(__name__)


def _repo_url_to_package(url: str) -> str | None:
    """Map a git repo URL to a PyPI package name via REVERSE_MAPPING or URL basename.

    :returns: Package name, or None if the URL has no usable basename.
    """
    if url in REVERSE_MAPPING:
        return REVERSE_MAPPING[url]
    last_segment = url.rstrip("/").rsplit("/", 1)[-1]
    return last_segment.lower() if last_segment else None


def _normalize_rev(rev: str) -> str | None:
    """Normalize a rev string to a comparable version, or None if unparseable.

    :returns: Normalized version string, or None for non-version revs.
    """
    stripped = rev.lstrip("v")
    try:
        return str(Version(stripped.replace("-", ".")))
    except InvalidVersion:
        try:
            return str(Version(stripped))
        except InvalidVersion:
            return None


def _prefetch_versions(
    package_names: set[str],
    repo_urls: set[str],
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
) -> tuple[dict[str, dict[str, str | None]], dict[str, list[str]]]:
    """Fetch PyPI versions and git tags in parallel.

    :param package_names: PyPI package names to look up.
    :param repo_urls: Git repository URLs to fetch tags from.
    :param index_url: Optional PEP 503 index URL.
    :param extra_index_urls: Additional PEP 503 index URLs to try.
    :param pip_config: Optional pip configuration for SSL settings.
    :returns: Tuple of (pypi_cache, git_cache) where pypi_cache maps package name to versions dict and
        git_cache maps repo URL to tag list.
    """
    logger.info(
        "Prefetching %d PyPI packages and %d git repos in parallel",
        len(package_names),
        len(repo_urls),
    )

    pypi_cache: dict[str, dict[str, str | None]] = {}
    git_cache: dict[str, list[str]] = {}

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        pypi_futures = {
            pool.submit(
                fetch_pypi_versions,
                name,
                index_url=index_url,
                extra_index_urls=extra_index_urls,
                pip_config=pip_config,
            ): name
            for name in package_names
        }
        git_futures = {pool.submit(fetch_git_tags, url): url for url in repo_urls}

        for pypi_future in as_completed(pypi_futures):
            name = pypi_futures[pypi_future]
            try:
                pypi_cache[name] = pypi_future.result()
            except FetchError:
                logger.warning("Failed to fetch PyPI versions for %s; skipping", name)
                pypi_cache[name] = {}

        for git_future in as_completed(git_futures):
            url = git_futures[git_future]
            try:
                git_cache[url] = git_future.result()
            except FetchError:
                logger.warning("Failed to fetch git tags for %s; skipping", url)
                git_cache[url] = []

    logger.debug(
        "Prefetched %d PyPI packages and %d git repos",
        len(pypi_cache),
        len(git_cache),
    )
    return pypi_cache, git_cache


def _log_convergence_result(
    pkg_name: str,
    target_version: str,
    *,
    is_pinned: bool,
    pyproject_changed: bool,
    needs_regen: bool,
    repo_rev: str,
    current_pyproject_version: str | None,
) -> None:
    """Log the convergence outcome for a shared main-hook package.

    :param pkg_name: Normalized package name.
    :param target_version: The version chosen as the convergence target.
    :param is_pinned: Whether the repo rev is explicitly pinned.
    :param pyproject_changed: Whether the pyproject version differs from target.
    :param needs_regen: Whether the pre-commit rev needs regeneration.
    :param repo_rev: The current rev string from .pre-commit-config.yaml.
    :param current_pyproject_version: The current version in pyproject.toml.
    """
    if pyproject_changed:
        logger.info(
            "  %s: %s → %s (pyproject%s%s)",
            pkg_name,
            current_pyproject_version,
            target_version,
            ", pinned" if is_pinned else "",
            ", stale rev" if needs_regen else "",
        )
    elif needs_regen:
        logger.info("  %s: stale rev %s (expected %s)", pkg_name, repo_rev, target_version)
    else:
        logger.info("  %s: %s (pinned, up to date)", pkg_name, target_version)


def _converge_shared_main_hooks(
    pyproject_deps: dict[str, list[PyProjectDependency]],
    precommit_repos: list[PreCommitRepo],
    repo_url_to_pkg: dict[str, str],
    pinned_revs: dict[str, str],
    processed_packages: set[str],
    processed_urls: set[str],
    *,
    pypi_cache: dict[str, dict[str, str | None]],
    git_cache: dict[str, list[str]],
    min_python: Version | None = None,
) -> list[ConvergenceResult]:
    """Converge packages that appear as both pyproject deps and pre-commit main hooks.

    :returns: List of convergence results for shared main-hook packages.
    """
    results: list[ConvergenceResult] = []

    for repo in precommit_repos:
        if repo.url not in repo_url_to_pkg:
            continue

        processed_urls.add(repo.url)
        pkg_name = repo_url_to_pkg[repo.url]
        dep_entries = pyproject_deps[pkg_name]
        current_pyproject_version = dep_entries[0].version

        logger.info("Converging shared hook: %s ↔ %s", pkg_name, repo.url)

        is_pinned = repo.url in pinned_revs
        if is_pinned:
            tag_str = pinned_revs[repo.url]
            target_version = tag_str.lstrip("v")
            logger.debug("  Using pinned rev %s → %s", tag_str, target_version)
        else:
            pypi_versions = pypi_cache.get(pkg_name, {})
            git_tags = git_cache.get(repo.url, [])
            common = find_highest_common_version(pypi_versions, git_tags, min_python=min_python)
            if not common:
                logger.warning("No common stable version for %s", pkg_name)
                processed_packages.add(pkg_name)
                continue
            tag_str, target_version = common

        normalized_rev = _normalize_rev(repo.rev)
        needs_regen = normalized_rev != target_version

        pyproject_changed = target_version != current_pyproject_version

        if pyproject_changed or is_pinned or needs_regen:
            results.append(
                ConvergenceResult(
                    package=pkg_name,
                    old_version=current_pyproject_version,
                    new_version=target_version,
                    target=UpdateTarget.PYPROJECT,
                    repo_url=repo.url,
                    groups=[d.group for d in dep_entries],
                    hook_ids=repo.hook_ids,
                    is_pinned=is_pinned,
                    needs_regeneration=needs_regen,
                    rev_tag=tag_str if needs_regen else None,
                ),
            )
            _log_convergence_result(
                pkg_name,
                target_version,
                is_pinned=is_pinned,
                pyproject_changed=pyproject_changed,
                needs_regen=needs_regen,
                repo_rev=repo.rev,
                current_pyproject_version=current_pyproject_version,
            )

        processed_packages.add(pkg_name)

    return results


def _converge_shared_additional_deps(
    pyproject_deps: dict[str, list[PyProjectDependency]],
    precommit_additional_names: dict[str, list[PreCommitRepo]],
    processed_packages: set[str],
    *,
    pypi_cache: dict[str, dict[str, str | None]],
    min_python: Version | None = None,
) -> list[ConvergenceResult]:
    """Converge packages shared between pyproject deps and pre-commit additional_dependencies.

    :returns: List of convergence results for shared additional-dependency packages.
    """
    results: list[ConvergenceResult] = []

    for ad_name, repos_with_ad in precommit_additional_names.items():
        if ad_name in processed_packages:
            continue
        if ad_name not in pyproject_deps:
            continue

        dep_entries = pyproject_deps[ad_name]
        current_version = dep_entries[0].version

        logger.info("Converging shared additional_dep: %s", ad_name)

        latest = resolve_latest_version(pypi_cache.get(ad_name, {}), min_python)
        if not latest:
            logger.warning("No stable PyPI version for %s", ad_name)
            processed_packages.add(ad_name)
            continue

        if latest != current_version:
            hook_ids: list[str] = [
                ad.hook_id for repo in repos_with_ad for ad in repo.additional_deps if ad.name == ad_name
            ]

            results.append(
                ConvergenceResult(
                    package=ad_name,
                    old_version=current_version,
                    new_version=latest,
                    target=UpdateTarget.BOTH,
                    groups=[d.group for d in dep_entries],
                    hook_ids=hook_ids,
                    is_additional_dep=True,
                ),
            )
            logger.info("  %s: %s → %s", ad_name, current_version, latest)

        processed_packages.add(ad_name)

    return results


def _converge_pypi_only(
    pyproject_deps: dict[str, list[PyProjectDependency]],
    processed_packages: set[str],
    pkg_to_repo_url: dict[str, str],
    precommit_additional_names: dict[str, list[PreCommitRepo]],
    *,
    pypi_cache: dict[str, dict[str, str | None]],
    min_python: Version | None = None,
) -> list[ConvergenceResult]:
    """Update pyproject-only packages to their latest stable PyPI version.

    :returns: List of convergence results for pyproject-only packages.
    """
    results: list[ConvergenceResult] = []

    for pkg_name, dep_entries in pyproject_deps.items():
        if pkg_name in processed_packages:
            continue
        if pkg_name in pkg_to_repo_url:
            continue
        if pkg_name in precommit_additional_names:
            continue

        current_version = dep_entries[0].version

        logger.debug("Checking PyPI-only: %s%s", pkg_name, f"=={current_version}" if current_version else "")

        latest = resolve_latest_version(pypi_cache.get(pkg_name, {}), min_python)
        if not latest or latest == current_version:
            processed_packages.add(pkg_name)
            continue

        results.append(
            ConvergenceResult(
                package=pkg_name,
                old_version=current_version,
                new_version=latest,
                target=UpdateTarget.PYPROJECT,
                groups=[d.group for d in dep_entries],
            ),
        )
        logger.info("  %s: %s → %s (pyproject only)", pkg_name, current_version, latest)
        processed_packages.add(pkg_name)

    return results


def _converge_precommit_only_additional(
    precommit_additional_names: dict[str, list[PreCommitRepo]],
    processed_packages: set[str],
    *,
    pypi_cache: dict[str, dict[str, str | None]],
    min_python: Version | None = None,
) -> list[ConvergenceResult]:
    """Update additional_dependencies that only appear in pre-commit config.

    :returns: List of convergence results for pre-commit-only additional dependencies.
    """
    results: list[ConvergenceResult] = []

    for ad_name, repos_with_ad in precommit_additional_names.items():
        if ad_name in processed_packages:
            continue

        logger.debug("Checking pre-commit-only additional_dep: %s", ad_name)

        current_version = None
        hook_ids: list[str] = []
        for repo in repos_with_ad:
            for ad in repo.additional_deps:
                if ad.name == ad_name:
                    current_version = current_version or ad.version
                    hook_ids.append(ad.hook_id)

        latest = resolve_latest_version(pypi_cache.get(ad_name, {}), min_python)
        if not latest or latest == current_version:
            processed_packages.add(ad_name)
            continue

        results.append(
            ConvergenceResult(
                package=ad_name,
                old_version=current_version,
                new_version=latest,
                target=UpdateTarget.GENPRECOMMIT,
                hook_ids=hook_ids,
                is_additional_dep=True,
            ),
        )
        logger.info(
            "  %s: %s → %s (pre-commit additional only)",
            ad_name,
            current_version,
            latest,
        )
        processed_packages.add(ad_name)

    return results


def _detect_stale_precommit_revs(
    precommit_repos: list[PreCommitRepo],
    pinned_revs: dict[str, str],
    processed_urls: set[str],
    *,
    git_cache: dict[str, list[str]],
) -> list[ConvergenceResult]:
    """Detect repos in .pre-commit-config.yaml with stale or invalid revs.

    Checks repos not already handled by shared-hook convergence. For each, compares the current rev against
    the pinned value or the latest stable git tag.

    :param precommit_repos: All parsed pre-commit repos.
    :param pinned_revs: Repo URL → pinned rev from .genprecommitconfig.yaml.
    :param processed_urls: URLs already handled by _converge_shared_main_hooks.
    :param git_cache: Pre-fetched git tags keyed by repo URL.
    :returns: List of ConvergenceResult for repos with stale revs.
    """
    results: list[ConvergenceResult] = []

    for repo in precommit_repos:
        if repo.url in processed_urls:
            continue

        repo_name = repo.url.rstrip("/").rsplit("/", 1)[-1]

        if repo.url in pinned_revs:
            tag_str = pinned_revs[repo.url]
            expected_version = tag_str.lstrip("v")
            normalized_rev = _normalize_rev(repo.rev)
            if normalized_rev == expected_version:
                continue
            results.append(
                ConvergenceResult(
                    package=repo_name,
                    old_version=repo.rev,
                    new_version=expected_version,
                    target=UpdateTarget.PYPROJECT,
                    repo_url=repo.url,
                    hook_ids=repo.hook_ids,
                    is_pinned=True,
                    needs_regeneration=True,
                    rev_tag=tag_str,
                ),
            )
            logger.info("  %s: stale rev %s (pinned %s)", repo_name, repo.rev, tag_str)
            continue

        sorted_tags = clean_and_sort_versions(git_cache.get(repo.url, []))
        if not sorted_tags:
            logger.debug("  %s: no stable tags found, skipping rev check", repo_name)
            continue

        tag_str, latest_version = sorted_tags[-1][0], str(sorted_tags[-1][1])
        normalized_rev = _normalize_rev(repo.rev)
        if normalized_rev == latest_version:
            continue

        results.append(
            ConvergenceResult(
                package=repo_name,
                old_version=repo.rev,
                new_version=latest_version,
                target=UpdateTarget.PYPROJECT,
                repo_url=repo.url,
                hook_ids=repo.hook_ids,
                needs_regeneration=True,
                rev_tag=tag_str,
            ),
        )
        logger.info("  %s: stale rev %s (latest %s)", repo_name, repo.rev, tag_str)

    return results


def _build_repo_mappings(
    pyproject_deps: dict[str, list[PyProjectDependency]],
    precommit_repos: list[PreCommitRepo],
) -> tuple[dict[str, str], dict[str, str], dict[str, list[PreCommitRepo]]]:
    """Build bidirectional repo-URL-to-package mappings and additional-dep index.

    :param pyproject_deps: Parsed dependencies from pyproject.toml.
    :param precommit_repos: Parsed repositories from .pre-commit-config.yaml.
    :returns: Tuple of (repo_url_to_pkg, pkg_to_repo_url, precommit_additional_names).
    """
    repo_url_to_pkg: dict[str, str] = {}
    pkg_to_repo_url: dict[str, str] = {}

    for repo in precommit_repos:
        pkg_name = _repo_url_to_package(repo.url)
        if pkg_name and pkg_name in pyproject_deps:
            repo_url_to_pkg[repo.url] = pkg_name
            pkg_to_repo_url[pkg_name] = repo.url

    precommit_additional_names: dict[str, list[PreCommitRepo]] = {}
    for repo in precommit_repos:
        for ad in repo.additional_deps:
            precommit_additional_names.setdefault(ad.name, []).append(repo)

    return repo_url_to_pkg, pkg_to_repo_url, precommit_additional_names


def _collect_prefetch_candidates(
    pyproject_deps: dict[str, list[PyProjectDependency]],
    precommit_repos: list[PreCommitRepo],
    repo_url_to_pkg: dict[str, str],
    pkg_to_repo_url: dict[str, str],
    precommit_additional_names: dict[str, list[PreCommitRepo]],
    pinned_revs: dict[str, str],
) -> tuple[set[str], set[str]]:
    """Determine which PyPI package names and git URLs need prefetching.

    :param pyproject_deps: Parsed dependencies from pyproject.toml.
    :param precommit_repos: Parsed repositories from .pre-commit-config.yaml.
    :param repo_url_to_pkg: Mapping of repo URL to package name.
    :param pkg_to_repo_url: Mapping of package name to repo URL.
    :param precommit_additional_names: Mapping of additional-dep name to repos.
    :param pinned_revs: Repo URL to rev string for explicitly pinned repos.
    :returns: Tuple of (pypi_names, git_urls) to prefetch.
    """
    pypi_names: set[str] = set()
    git_urls: set[str] = set()

    for url, pkg in repo_url_to_pkg.items():
        if url not in pinned_revs:
            pypi_names.add(pkg)
            git_urls.add(url)

    pypi_names.update(precommit_additional_names)

    for pkg_name in pyproject_deps:
        if pkg_name not in pkg_to_repo_url and pkg_name not in precommit_additional_names:
            pypi_names.add(pkg_name)

    for repo in precommit_repos:
        if repo.url not in repo_url_to_pkg and repo.url not in pinned_revs:
            git_urls.add(repo.url)

    return pypi_names, git_urls


def converge(
    pyproject_deps: dict[str, list[PyProjectDependency]],
    precommit_repos: list[PreCommitRepo],
    pinned_revs: dict[str, str],
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
    min_python: Version | None = None,
) -> list[ConvergenceResult]:
    """Run the bidirectional convergence algorithm.

    Revs in ``.genprecommitconfig.yaml`` are intentional pins and are never modified.  For shared main hooks
    the pinned (or latest-resolved) rev is treated as the authoritative version and ``pyproject.toml`` is
    updated to match.  Only ``additional_dependencies`` are updated in the genprecommit config.

    :param pyproject_deps: Parsed dependencies from pyproject.toml.
    :type pyproject_deps: dict[str, list[PyProjectDependency]]
    :param precommit_repos: Parsed repositories from .pre-commit-config.yaml.
    :type precommit_repos: list[PreCommitRepo]
    :param pinned_revs: Repo URL → rev string for explicitly pinned repos in .genprecommitconfig.yaml.
    :type pinned_revs: dict[str, str]
    :param index_url: Optional PEP 503 package index URL to query before falling back to public PyPI.
    :type index_url: str | None
    :param extra_index_urls: Additional PEP 503 index URLs to try.
    :type extra_index_urls: Sequence[str]
    :param pip_config: Optional pip configuration for SSL settings.
    :type pip_config: PipConfig | None
    :param min_python: Minimum Python version to filter compatible releases.
    :type min_python: Version | None
    :returns: List of ConvergenceResult describing all updates needed.
    :rtype: list[ConvergenceResult]
    """
    results: list[ConvergenceResult] = []

    repo_url_to_pkg, pkg_to_repo_url, precommit_additional_names = _build_repo_mappings(
        pyproject_deps,
        precommit_repos,
    )

    pypi_names, git_urls = _collect_prefetch_candidates(
        pyproject_deps,
        precommit_repos,
        repo_url_to_pkg,
        pkg_to_repo_url,
        precommit_additional_names,
        pinned_revs,
    )

    pypi_cache, git_cache = _prefetch_versions(
        pypi_names,
        git_urls,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
    )

    processed_packages: set[str] = set()
    processed_urls: set[str] = set()

    results.extend(
        _converge_shared_main_hooks(
            pyproject_deps,
            precommit_repos,
            repo_url_to_pkg,
            pinned_revs,
            processed_packages,
            processed_urls,
            pypi_cache=pypi_cache,
            git_cache=git_cache,
            min_python=min_python,
        ),
    )

    results.extend(
        _converge_shared_additional_deps(
            pyproject_deps,
            precommit_additional_names,
            processed_packages,
            pypi_cache=pypi_cache,
            min_python=min_python,
        ),
    )

    results.extend(
        _converge_pypi_only(
            pyproject_deps,
            processed_packages,
            pkg_to_repo_url,
            precommit_additional_names,
            pypi_cache=pypi_cache,
            min_python=min_python,
        ),
    )

    results.extend(
        _converge_precommit_only_additional(
            precommit_additional_names,
            processed_packages,
            pypi_cache=pypi_cache,
            min_python=min_python,
        ),
    )

    results.extend(
        _detect_stale_precommit_revs(
            precommit_repos,
            pinned_revs,
            processed_urls,
            git_cache=git_cache,
        ),
    )

    return results


def _parse_mypy_types(pyproject_path: Path) -> dict[str, str | None]:
    """Extract types-* entries from the type-stubs optional-dependency group.

    :returns: Dict mapping normalized types-* package name to its pinned version (or None if unpinned).
    :raises ParseError: If the file cannot be read or contains invalid TOML.
    """
    try:
        data = load_toml(pyproject_path)
    except ToolError as exc:
        raise ParseError(str(exc)) from exc

    mypy_deps = data.get("project", {}).get("optional-dependencies", {}).get("type-stubs", [])
    types_map: dict[str, str | None] = {}
    for dep_str in mypy_deps:
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

    :param to_check: Base package names to check.
    :param index_url: Optional PEP 503 index URL.
    :param extra_index_urls: Additional PEP 503 index URLs to try.
    :param pip_config: Optional pip configuration for SSL settings.
    :returns: Set of base package names whose types-* stub exists.
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
    """Build the set of types-* package names whose versions need fetching."""
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
    """Identify types-* stubs to add."""
    added: list[tuple[str, str]] = []
    for name in sorted(available):
        types_name = f"types-{name}"
        if types_name not in current_types:
            latest = resolve_latest_version(types_cache.get(types_name, {}), min_python)
            if latest:
                added.append((types_name, latest))
                logger.info("  Add %s==%s", types_name, latest)
    return added


def _find_stale_stubs(
    current_types: dict[str, str | None],
    all_packages: set[str],
    types_cache: dict[str, dict[str, str | None]],
    min_python: Version | None,
) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Identify types-* stubs to remove or update."""
    removed: list[str] = []
    updated: list[tuple[str, str, str]] = []
    for types_name, current_version in sorted(current_types.items()):
        base_name = types_name.removeprefix("types-")
        if base_name not in all_packages:
            removed.append(types_name)
            logger.info("  Remove %s (base package not in dependency tree)", types_name)
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
) -> TypesSyncResult:
    """Compute types-* stub additions, removals, and updates.

    :param base_packages: Non-types package names from uv.lock.
    :type base_packages: set[str]
    :param all_packages: All package names from uv.lock (including types-*).
    :type all_packages: set[str]
    :param pyproject_path: Path to pyproject.toml.
    :type pyproject_path: Path
    :param index_url: Optional PEP 503 index URL.
    :type index_url: str | None
    :param extra_index_urls: Additional PEP 503 index URLs to try.
    :type extra_index_urls: Sequence[str]
    :param pip_config: Optional pip configuration for SSL settings.
    :type pip_config: PipConfig | None
    :param min_python: Minimum Python version to filter compatible releases.
    :type min_python: Version | None
    :returns: TypesSyncResult describing all changes.
    :rtype: TypesSyncResult
    """
    current_types = _parse_mypy_types(pyproject_path)

    candidates = {name for name in base_packages if not name.startswith(PROJECT_NAME) and name != "mypy"}

    already_known = {name.removeprefix("types-") for name in current_types}
    to_check = candidates - already_known

    logger.info(
        "Checking %d candidates for types-* stubs (%d already in type-stubs group)",
        len(to_check),
        len(already_known),
    )

    available = _discover_available_types(
        to_check,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
    )

    types_to_fetch = _collect_types_to_fetch(available, current_types, all_packages)
    types_cache, _ = _prefetch_versions(
        types_to_fetch,
        set(),
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
    )

    result = TypesSyncResult()
    result.added = _find_new_stubs(available, current_types, types_cache, min_python)
    result.removed, result.updated = _find_stale_stubs(current_types, all_packages, types_cache, min_python)

    return result

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Git tag version discovery for pre-commit repositories."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import importlib.metadata
import logging
import operator
import re

from depsync.config import REVERSE_MAPPING
from depsync.fetchers import fetch_pypi_versions, find_highest_common_version
from packaging.version import InvalidVersion, Version
from precommit.exceptions import DiscoveryError
from shared.git import GitCommandError, run_ls_remote
from shared.pip_config import PipConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RevisionResult:
    """Resolved revision with the full list of candidate tags."""

    rev: str
    candidates: list[str] = field(default_factory=list)


_TAG_REF_PATTERN = re.compile(r"^[0-9a-f]{40}\s+refs/tags/(.+)$")
_PRERELEASE_PATTERN = re.compile(r"\d[ab]\d")
_MIN_PARTS = 2


def _resolve_installed_version(repo_url: str) -> str:
    """Resolve version from the installed package matching the repo name.

    Args:
        repo_url: Repository URL to extract package name from.

    Returns:
        Installed package version string.

    Raises:
        DiscoveryError: If the package is not installed.
    """
    package_name = repo_url.rsplit("/", maxsplit=1)[-1].replace("-pre-commit", "")
    try:
        version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError as exc:
        msg = f"Package '{package_name}' is not installed (from {repo_url})"
        raise DiscoveryError(msg) from exc

    logger.info("%s : %s (from installed %s)", repo_url, version, package_name)
    return version


def _find_highest_available_tag(
    tags: list[str],
    pypi_name: str,
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
    min_python: Version | None = None,
) -> tuple[str, str] | None:
    """Find the highest git tag whose version is available on PyPI.

    Args:
        tags: Raw git tag strings.
        pypi_name: PyPI package name to query.
        index_url: Optional PEP 503 index URL.
        extra_index_urls: Additional PEP 503 index URLs to try.
        pip_config: Optional pip configuration for SSL settings.
        min_python: Minimum Python version to filter against.

    Returns:
        Tuple of (original_tag, normalized_version) or None if no match.
    """
    pypi_versions = fetch_pypi_versions(
        pypi_name,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
    )
    if not pypi_versions:
        return None

    return find_highest_common_version(pypi_versions, tags, min_python=min_python)


def _parse_tags(ls_remote_output: str) -> list[str]:
    """Parse git ls-remote --tags output into a list of tag names.

    Filters out annotated-tag dereferences (``^{}``) and pre-release tags.

    Args:
        ls_remote_output: Raw stdout from git ls-remote.

    Returns:
        List of release tag names.
    """
    tags: list[str] = []
    for line in ls_remote_output.strip().splitlines():
        if line.endswith("^{}"):
            continue

        match = _TAG_REF_PATTERN.match(line)
        if not match:
            continue

        tag = match.group(1)
        if _PRERELEASE_PATTERN.search(tag):
            continue

        tags.append(tag)

    return tags


def _normalize_version(tag: str) -> str:
    """Strip common version prefixes for comparison.

    Args:
        tag: Raw tag name.

    Returns:
        Numeric version string with v/ver prefix removed.
    """
    return re.sub(r"^(ver|v)", "", tag, flags=re.IGNORECASE)


def _select_latest_tag(tags: list[str]) -> str:
    """Select the latest tag by PEP 440 version sorting.

    Falls back to string sorting if version parsing fails for all tags.

    Args:
        tags: List of tag names.

    Returns:
        The tag name with the highest version.
    """
    versioned: list[tuple[Version, str]] = []
    for tag in tags:
        try:
            ver = Version(_normalize_version(tag))
            versioned.append((ver, tag))
        except InvalidVersion:
            logger.debug("Skipping unparseable tag: %s", tag)

    if versioned:
        versioned.sort(key=operator.itemgetter(0))
        return versioned[-1][1]

    tags.sort()
    return tags[-1]


def _sort_tags_descending(tags: list[str]) -> list[str]:
    """Sort tags newest-first by PEP 440 version.

    Args:
        tags: List of tag names.

    Returns:
        Tags sorted from newest to oldest. Unparseable tags are
        excluded.
    """
    versioned: list[tuple[Version, str]] = []
    for tag in tags:
        try:
            ver = Version(_normalize_version(tag))
            versioned.append((ver, tag))
        except InvalidVersion:
            logger.debug("Skipping unparseable tag: %s", tag)

    versioned.sort(key=operator.itemgetter(0), reverse=True)
    return [tag for _, tag in versioned]


def _resolve_head_commit(repo_url: str) -> str:
    """Resolve HEAD commit hash when no tags are available.

    Args:
        repo_url: Remote repository URL.

    Returns:
        HEAD commit SHA.

    Raises:
        DiscoveryError: If the git command fails.
    """
    try:
        result = run_ls_remote(repo_url, "--quiet", refspecs=("HEAD",))
    except GitCommandError as exc:
        raise DiscoveryError(str(exc)) from exc

    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= _MIN_PARTS and parts[1] == "HEAD":
            rev = parts[0]
            logger.info("%s : %s (HEAD)", repo_url, rev)
            return rev

    msg = f"No HEAD ref found for {repo_url}"
    raise DiscoveryError(msg)


def _resolve_latest_tag(
    repo_url: str,
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
    min_python: Version | None = None,
) -> RevisionResult:
    """Resolve the latest release tag from a remote git repository.

    Runs ``git ls-remote --tags`` and parses the output in Python, filtering out pre-release tags and
    annotated-tag dereferences.  When the repository URL maps to a known PyPI package, cross-references git
    tags against available versions on the configured package index and falls back through tags until an
    available version is found.

    Args:
        repo_url: Remote repository URL.
        index_url: Optional PEP 503 index URL for availability checks.
        min_python: Minimum Python version to filter compatible
            releases.

    Returns:
        RevisionResult with the latest tag and all sorted candidates.

    Raises:
        DiscoveryError: If no tags are found or the git command fails.
    """
    try:
        result = run_ls_remote(repo_url, "--tags", "--quiet")
    except GitCommandError as exc:
        raise DiscoveryError(str(exc)) from exc

    tags = _parse_tags(result.stdout)

    if not tags:
        rev = _resolve_head_commit(repo_url)
        return RevisionResult(rev=rev)

    sorted_tags = _sort_tags_descending(tags)

    pypi_name = REVERSE_MAPPING.get(repo_url)
    if pypi_name:
        common = _find_highest_available_tag(
            tags,
            pypi_name,
            index_url=index_url,
            extra_index_urls=extra_index_urls,
            pip_config=pip_config,
            min_python=min_python,
        )
        if common:
            tag_str, _version = common
            logger.info("%s : %s (highest available on index)", repo_url, tag_str)
            return RevisionResult(rev=tag_str, candidates=sorted_tags)
        logger.warning(
            "No index-available version found for %s (%s); using latest git tag",
            pypi_name,
            repo_url,
        )

    best_tag = _select_latest_tag(tags)
    logger.info("%s : %s", repo_url, best_tag)
    return RevisionResult(rev=best_tag, candidates=sorted_tags)


def resolve_revision(
    repo_url: str,
    rev_spec: str | None,
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
    min_python: Version | None = None,
) -> RevisionResult:
    """Resolve a repository revision from a spec.

    Args:
        repo_url (str): Repository URL.
        rev_spec (str | None): Revision specification: None for latest
            tag, "installed" for installed package version, or an exact
            version string.
        index_url (str | None): Optional PEP 503 package index URL to
            cross-reference tag availability.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs
            to try.
        pip_config (PipConfig | None): Optional pip configuration for
            SSL settings.
        min_python (Version | None): Minimum Python version to filter
            compatible releases.

    Returns:
        RevisionResult: RevisionResult with the resolved revision and
        candidate tags.
    """
    if rev_spec is not None and rev_spec != "installed":
        logger.info("%s : %s (pinned)", repo_url, rev_spec)
        return RevisionResult(rev=rev_spec)

    if rev_spec == "installed":
        rev = _resolve_installed_version(repo_url)
        return RevisionResult(rev=rev)

    return _resolve_latest_tag(
        repo_url,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
        min_python=min_python,
    )

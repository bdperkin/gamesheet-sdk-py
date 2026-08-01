# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Version discovery via PyPI JSON API, PEP 503 Simple API, and git ls-remote."""

from __future__ import annotations

from collections.abc import Sequence
from html.parser import HTMLParser
import logging
import operator
import re

from depsync.config import (
    PYPI_API_URL,
    PYPI_TIMEOUT,
)
from depsync.exceptions import FetchError
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import InvalidVersion, Version
import requests
from shared.git import GitCommandError, run_ls_remote
from shared.http_client import get_session
from shared.pip_config import PipConfig, resolve_verify

logger = logging.getLogger(__name__)


class _SimpleIndexParser(HTMLParser):
    """Parse filenames and requires-python from PEP 503 Simple Repository API HTML."""

    def __init__(self: _SimpleIndexParser) -> None:
        super().__init__()
        self.files: list[tuple[str, str | None]] = []

    def handle_starttag(self: _SimpleIndexParser, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = None
        req_py = None
        for attr, value in attrs:
            if attr == "href" and value:
                href = value.rsplit("#", 1)[0].rsplit("/", 1)[-1]
            elif attr == "data-requires-python" and value:
                req_py = value
        if href:
            self.files.append((href, req_py))


def _version_from_filename(filename: str) -> str | None:
    """Extract a version string from a wheel or sdist filename.

    :returns: Version string, or None if the filename cannot be parsed.
    """
    try:
        if filename.endswith(".whl"):
            _, ver, _, _ = parse_wheel_filename(filename)
            return str(ver)
        if filename.endswith((".tar.gz", ".zip")):
            _, ver = parse_sdist_filename(filename)
            return str(ver)
    except (InvalidWheelFilename, InvalidSdistFilename):
        logger.debug("Could not parse version from filename: %s", filename)
    return None


def _extract_versions_from_simple_html(html_content: str) -> dict[str, str | None]:
    """Extract version strings and requires-python from Simple API HTML.

    :returns: Dict mapping version string to requires_python (or None).
    """
    parser = _SimpleIndexParser()
    parser.feed(html_content)

    versions: dict[str, str | None] = {}
    for filename, req_py in parser.files:
        ver = _version_from_filename(filename)
        if ver and ver not in versions:
            versions[ver] = req_py

    return versions


_SIMPLE_ACCEPT = (
    "application/vnd.pypi.simple.v1+json;q=1, application/vnd.pypi.simple.v1+html;q=0.5, text/html;q=0.01"
)


def _extract_versions_from_simple_json(data: dict) -> dict[str, str | None]:  # type: ignore[type-arg]
    """Extract versions and requires-python from a PEP 691 JSON response.

    :returns: Dict mapping version string to requires_python (or None).
    """
    req_py_map: dict[str, str | None] = {}

    for file_entry in data.get("files", []):
        ver = _version_from_filename(file_entry.get("filename", ""))
        if ver and ver not in req_py_map:
            req_py_map[ver] = file_entry.get("requires-python")

    if "versions" in data:
        for ver in data["versions"]:
            if ver not in req_py_map:
                req_py_map[ver] = None

    return req_py_map


def _parse_simple_response(
    response: requests.Response,
    content_type: str,
    package_name: str,
    index_url: str,
) -> dict[str, str | None]:
    """Parse a Simple API response into a version dict.

    :returns: Dict mapping version string to requires_python (or None), empty on failure.
    """
    try:
        if "json" in content_type:
            versions = _extract_versions_from_simple_json(response.json())
        else:
            versions = _extract_versions_from_simple_html(response.text)
    except (ValueError, KeyError, TypeError):
        logger.warning("Failed to parse index response for %s at %s", package_name, index_url)
        return {}
    return versions


def _fetch_simple_versions(
    package_name: str,
    index_url: str,
    *,
    pip_config: PipConfig | None = None,
) -> dict[str, str | None]:
    """Fetch versions from a PEP 503/691 Simple Repository API.

    Requests PEP 691 JSON (preferred) with HTML fallback so that proxy repositories like Nexus return complete
    listings.

    :returns: Dict mapping version string to requires_python (or None), empty on failure.
    """
    normalized = re.sub(r"[-_.]+", "-", package_name).lower()
    base = index_url.rstrip("/")
    url = f"{base}/{normalized}/"

    session = get_session()
    try:
        # verify may be False for pip trusted-host entries — intentional, mirrors pip semantics
        response = session.get(
            url,
            timeout=PYPI_TIMEOUT,
            verify=resolve_verify(url, pip_config),
            headers={"Accept": _SIMPLE_ACCEPT},
        )
        if response.status_code == 404:
            logger.debug("Package %s not found on index %s", package_name, index_url)
            return {}
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Index query failed for %s at %s: %s", package_name, index_url, exc)
        return {}

    content_type = response.headers.get("content-type", "")
    versions = _parse_simple_response(response, content_type, package_name, index_url)

    logger.debug("Fetched %d versions for %s from index", len(versions), package_name)
    return versions


def check_package_exists(
    package_name: str,
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
) -> bool:
    """Check whether a package exists on the configured index or PyPI.

    Respects pip semantics: when *index_url* is set, only that index and any *extra_index_urls* are queried.
    Public PyPI is used only when no index is configured at all.

    :param package_name: The package name to look up.
    :type package_name: str
    :param index_url: Optional PEP 503 Simple API base URL.
    :type index_url: str | None
    :param extra_index_urls: Additional PEP 503 index URLs to try.
    :type extra_index_urls: Sequence[str]
    :param pip_config: Optional pip configuration for SSL settings.
    :type pip_config: PipConfig | None
    :returns: True if the package exists, False otherwise.
    :rtype: bool
    """
    if index_url:
        versions = _fetch_simple_versions(package_name, index_url, pip_config=pip_config)
        if versions:
            return True

    for extra_url in extra_index_urls:
        versions = _fetch_simple_versions(package_name, extra_url, pip_config=pip_config)
        if versions:
            return True

    if index_url or extra_index_urls:
        return False

    url = PYPI_API_URL.format(package=package_name)
    session = get_session()
    try:
        response = session.head(url, timeout=PYPI_TIMEOUT)
    except requests.RequestException:
        return False
    return response.status_code == 200


def _extract_requires_python(files: list[dict[str, str | None]]) -> str | None:
    """Extract the first non-empty requires_python from a list of release file entries.

    :param files: Release file metadata dicts from the PyPI JSON API.
    :type files: list[dict[str, str | None]]
    :returns: The first requires_python string found, or None.
    :rtype: str | None
    """
    for f in files:
        rp = f.get("requires_python")
        if rp:
            return rp
    return None


def _fetch_pypi_json_versions(package_name: str) -> dict[str, str | None]:
    """Fetch versions from the public PyPI JSON API.

    :param package_name: The PyPI package name.
    :type package_name: str
    :returns: Dict mapping version string to requires_python (or None).
    :rtype: dict[str, str | None]
    :raises FetchError: If the request fails.
    """
    url = PYPI_API_URL.format(package=package_name)
    session = get_session()
    try:
        response = session.get(url, timeout=PYPI_TIMEOUT)
        if response.status_code == 404:
            logger.warning("Package %s not found on PyPI", package_name)
            return {}
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        msg = f"Failed to fetch PyPI versions for {package_name}: {exc}"
        raise FetchError(msg) from exc

    return {ver: _extract_requires_python(files) for ver, files in data.get("releases", {}).items()}


def fetch_pypi_versions(
    package_name: str,
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
) -> dict[str, str | None]:
    """Fetch all release versions and their requires-python metadata.

    Respects pip semantics: when *index_url* is set, only that index and any *extra_index_urls* are queried.
    Public PyPI is used only when no index is configured at all.

    :param package_name: The PyPI package name.
    :type package_name: str
    :param index_url: Optional PEP 503 Simple API base URL.
    :type index_url: str | None
    :param extra_index_urls: Additional PEP 503 index URLs to try.
    :type extra_index_urls: Sequence[str]
    :param pip_config: Optional pip configuration for SSL settings.
    :type pip_config: PipConfig | None
    :returns: Dict mapping version string to requires_python (or None).
    :rtype: dict[str, str | None]
    :raises FetchError: If all fetch attempts fail.
    """
    if index_url:
        versions = _fetch_simple_versions(package_name, index_url, pip_config=pip_config)
        if versions:
            return versions
        logger.debug("Primary index returned no results for %s", package_name)

    for extra_url in extra_index_urls:
        versions = _fetch_simple_versions(package_name, extra_url, pip_config=pip_config)
        if versions:
            return versions

    if index_url or extra_index_urls:
        logger.debug("No configured index returned results for %s", package_name)
        return {}

    logger.debug("No index configured; querying public PyPI for %s", package_name)

    return _fetch_pypi_json_versions(package_name)


def fetch_git_tags(repo_url: str) -> list[str]:
    """Fetch all tags from a git repository via ls-remote.

    :param repo_url: The HTTPS git repository URL.
    :type repo_url: str
    :returns: List of tag strings (deduplicated, without ^{} suffixes).
    :rtype: list[str]
    :raises FetchError: If the git command fails.
    """
    try:
        result = run_ls_remote(repo_url, "--tags")
    except GitCommandError as exc:
        raise FetchError(str(exc)) from exc

    tags: list[str] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("refs/tags/")
        if len(parts) > 1:
            tag = parts[1].replace("^{}", "")
            if tag not in tags:
                tags.append(tag)

    logger.debug("Fetched %d tags from %s", len(tags), repo_url)
    return tags


def clean_and_sort_versions(
    version_list: list[str],
    *,
    include_prerelease: bool = False,
) -> list[tuple[str, Version]]:
    """Filter and sort version strings.

    :param version_list: Raw version strings (may include 'v' prefix).
    :type version_list: list[str]
    :param include_prerelease: If True, include pre-release and dev versions.
    :type include_prerelease: bool
    :returns: Sorted list of (original_string, parsed_Version) tuples, ascending.
    :rtype: list[tuple[str, Version]]
    """
    valid: list[tuple[str, Version]] = []
    for v in version_list:
        stripped = v.lstrip("v")
        try:
            parsed = Version(stripped.replace("-", "."))
        except InvalidVersion:
            try:
                parsed = Version(stripped)
            except InvalidVersion:
                continue
        if not include_prerelease and (parsed.is_prerelease or parsed.is_devrelease):
            continue
        valid.append((v, parsed))
    valid.sort(key=operator.itemgetter(1))
    return valid


def filter_python_compatible(
    versions: dict[str, str | None],
    min_python: Version | None,
) -> list[str]:
    """Filter versions to those compatible with the minimum Python version.

    :param versions: Dict mapping version string to requires_python (or None).
    :type versions: dict[str, str | None]
    :param min_python: Minimum Python version the project supports, or None to skip filtering.
    :type min_python: Version | None
    :returns: List of compatible version strings.
    :rtype: list[str]
    """
    if min_python is None:
        return list(versions.keys())

    compatible: list[str] = []
    for ver, req_py in versions.items():
        if req_py is None:
            compatible.append(ver)
            continue
        try:
            if min_python in SpecifierSet(req_py):
                compatible.append(ver)
            else:
                logger.debug(
                    "  Skipping %s (requires_python=%s, need %s)",
                    ver,
                    req_py,
                    min_python,
                )
        except InvalidSpecifier:
            compatible.append(ver)
    return compatible


def resolve_latest_version(
    versions: dict[str, str | None],
    min_python: Version | None,
) -> str | None:
    """Pick the latest stable version from a pre-fetched versions dict.

    Falls back to the latest pre-release if no stable version exists. Filters out versions incompatible with
    *min_python* when set.

    :param versions: Mapping of version string to requires_python (or None).
    :type versions: dict[str, str | None]
    :param min_python: Minimum Python version to filter against.
    :type min_python: Version | None
    :returns: The latest version string, or None if none found.
    :rtype: str | None
    """
    compatible = filter_python_compatible(versions, min_python)
    sorted_versions = clean_and_sort_versions(compatible)
    if not sorted_versions:
        sorted_versions = clean_and_sort_versions(compatible, include_prerelease=True)
    if not sorted_versions:
        return None
    return str(sorted_versions[-1][1])


def find_highest_common_version(
    pypi_versions: dict[str, str | None],
    git_tags: list[str],
    *,
    min_python: Version | None = None,
) -> tuple[str, str] | None:
    """Find the highest version present in both PyPI releases and git tags.

    :param pypi_versions: Dict mapping version string to requires_python.
    :type pypi_versions: dict[str, str | None]
    :param git_tags: Tag strings from git ls-remote.
    :type git_tags: list[str]
    :param min_python: Minimum Python version to filter against.
    :type min_python: Version | None
    :returns: Tuple of (git_tag_string, normalized_version) for the highest common stable version, or None if
        no overlap.
    :rtype: tuple[str, str] | None
    """
    compatible = filter_python_compatible(pypi_versions, min_python)
    pypi_sorted = clean_and_sort_versions(compatible)
    git_sorted = clean_and_sort_versions(git_tags)

    pypi_set = {str(parsed) for _, parsed in pypi_sorted}

    for orig_tag, parsed_tag in reversed(git_sorted):
        if str(parsed_tag) in pypi_set:
            return orig_tag, str(parsed_tag)

    return None

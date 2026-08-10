# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Version discovery via PyPI JSON API, PEP 503 Simple API, and git ls-remote."""

from __future__ import annotations

from collections.abc import Sequence
from html.parser import HTMLParser
import http
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
    """Parse filenames, requires-python, and yank status from PEP 503 Simple API HTML."""

    def __init__(self: _SimpleIndexParser) -> None:
        super().__init__()
        self.files: list[tuple[str, str | None, bool]] = []

    def handle_starttag(
        self: _SimpleIndexParser,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "a":
            return

        href = None
        req_py = None
        yanked = False
        for attr, value in attrs:
            if attr == "href" and value:
                href = value.rsplit("#", 1)[0].rsplit("/", 1)[-1]
            elif attr == "data-requires-python" and value:
                req_py = value
            elif attr == "data-yanked":
                # PEP 592: the attribute's presence marks the file yanked; its value is only a reason.
                yanked = True

        if href:
            self.files.append((href, req_py, yanked))


def _version_from_filename(filename: str) -> str | None:
    """Extract a version string from a wheel or sdist filename.

    Returns:
        str | None: Version string, or None if the filename cannot be parsed.
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


def _drop_yanked(
    versions: dict[str, str | None],
    yanked: dict[str, bool],
) -> dict[str, str | None]:
    """Remove releases whose every distribution is yanked.

    A yanked release is only installable when a requirement pins it exactly (PEP 592), so proposing one as a
    convergence target produces a pin that resolvers refuse to reach — and that cannot later be relaxed to
    discover an upgrade.

    Args:
        versions (dict[str, str | None]): Version string to requires_python.
        yanked (dict[str, bool]): Version string to whether every file for it is yanked.

    Returns:
        dict[str, str | None]: The input with fully-yanked releases removed.
    """
    kept = {ver: req_py for ver, req_py in versions.items() if not yanked.get(ver)}

    dropped = len(versions) - len(kept)
    if dropped:
        logger.debug("Excluded %d yanked release(s) from candidates", dropped)

    return kept


def _extract_versions_from_simple_html(html_content: str) -> dict[str, str | None]:
    """Extract version strings and requires-python from Simple API HTML.

    Returns:
        dict[str, str | None]: Dict mapping version string to requires_python (or None), yanked releases
            excluded.
    """
    parser = _SimpleIndexParser()
    parser.feed(html_content)

    versions: dict[str, str | None] = {}
    yanked: dict[str, bool] = {}
    for filename, req_py, is_yanked in parser.files:
        ver = _version_from_filename(filename)
        if not ver:
            continue

        if ver not in versions:
            versions[ver] = req_py

        yanked[ver] = yanked.get(ver, True) and is_yanked

    return _drop_yanked(versions, yanked)


_SIMPLE_ACCEPT = (
    "application/vnd.pypi.simple.v1+json;q=1, application/vnd.pypi.simple.v1+html;q=0.5, text/html;q=0.01"
)


def _extract_versions_from_simple_json(data: dict) -> dict[str, str | None]:  # type: ignore[type-arg]
    """Extract versions and requires-python from a PEP 691 JSON response.

    Returns:
        dict[str, str | None]: Dict mapping version string to requires_python (or None), yanked releases
            excluded.
    """
    req_py_map: dict[str, str | None] = {}
    yanked: dict[str, bool] = {}

    for file_entry in data.get("files", []):
        ver = _version_from_filename(file_entry.get("filename", ""))
        if not ver:
            continue

        if ver not in req_py_map:
            req_py_map[ver] = file_entry.get("requires-python")

        yanked[ver] = yanked.get(ver, True) and bool(file_entry.get("yanked"))

    if "versions" in data:
        for ver in data["versions"]:
            if ver not in req_py_map:
                req_py_map[ver] = None

    return _drop_yanked(req_py_map, yanked)


def _parse_simple_response(
    response: requests.Response,
    content_type: str,
    package_name: str,
    index_url: str,
) -> dict[str, str | None]:
    """Parse a Simple API response into a version dict.

    Returns:
        dict[str, str | None]: Dict mapping version string to requires_python (or None), empty on failure.
    """
    try:
        if "json" in content_type:
            versions = _extract_versions_from_simple_json(response.json())
        else:
            versions = _extract_versions_from_simple_html(response.text)
    except (ValueError, KeyError, TypeError):
        logger.warning(
            "Failed to parse index response for %s at %s",
            package_name,
            index_url,
        )
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

    Returns:
        dict[str, str | None]: Dict mapping version string to requires_python (or None), empty on failure.
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
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            logger.debug("Package %s not found on index %s", package_name, index_url)
            return {}

        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning(
            "Index query failed for %s at %s: %s",
            package_name,
            index_url,
            exc,
        )
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

    Args:
        package_name (str): The package name to look up.
        index_url (str | None): Optional PEP 503 Simple API base URL.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs to try.
        pip_config (PipConfig | None): Optional pip configuration for SSL settings.

    Returns:
        bool: True if the package exists, False otherwise.
    """
    if index_url:
        versions = _fetch_simple_versions(
            package_name,
            index_url,
            pip_config=pip_config,
        )
        if versions:
            return True

    for extra_url in extra_index_urls:
        versions = _fetch_simple_versions(
            package_name,
            extra_url,
            pip_config=pip_config,
        )
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

    return response.status_code == http.HTTPStatus.OK


def _extract_requires_python(files: list[dict[str, str | None]]) -> str | None:
    """Extract the first non-empty requires_python from a list of release file entries.

    Args:
        files (list[dict[str, str | None]]): Release file metadata dicts from the PyPI JSON API.

    Returns:
        str | None: The first requires_python string found, or None.
    """
    for f in files:
        rp = f.get("requires_python")
        if rp:
            return rp

    return None


def _fetch_pypi_json_versions(package_name: str) -> dict[str, str | None]:
    """Fetch versions from the public PyPI JSON API.

    Args:
        package_name (str): The PyPI package name.

    Returns:
        dict[str, str | None]: Dict mapping version string to requires_python (or None), yanked releases
            excluded.

    Raises:
        FetchError: If the request fails.
    """
    url = PYPI_API_URL.format(package=package_name)
    session = get_session()
    try:
        response = session.get(url, timeout=PYPI_TIMEOUT)
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            logger.warning("Package %s not found on PyPI", package_name)
            return {}

        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        msg = f"Failed to fetch PyPI versions for {package_name}: {exc}"
        raise FetchError(msg) from exc

    releases = data.get("releases", {})
    versions = {ver: _extract_requires_python(files) for ver, files in releases.items()}
    yanked = {ver: bool(files) and all(f.get("yanked") for f in files) for ver, files in releases.items()}

    return _drop_yanked(versions, yanked)


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

    Args:
        package_name (str): The PyPI package name.
        index_url (str | None): Optional PEP 503 Simple API base URL.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs to try.
        pip_config (PipConfig | None): Optional pip configuration for SSL settings.

    Returns:
        dict[str, str | None]: Dict mapping version string to requires_python (or None).

    Raises:
        FetchError: If all fetch attempts fail.
    """
    if index_url:
        versions = _fetch_simple_versions(
            package_name,
            index_url,
            pip_config=pip_config,
        )
        if versions:
            return versions

        logger.debug("Primary index returned no results for %s", package_name)

    for extra_url in extra_index_urls:
        versions = _fetch_simple_versions(
            package_name,
            extra_url,
            pip_config=pip_config,
        )
        if versions:
            return versions

    if index_url or extra_index_urls:
        logger.debug("No configured index returned results for %s", package_name)
        return {}

    logger.debug("No index configured; querying public PyPI for %s", package_name)

    return _fetch_pypi_json_versions(package_name)


def fetch_git_tags(repo_url: str) -> list[str]:
    """Fetch all tags from a git repository via ls-remote.

    Args:
        repo_url (str): The HTTPS git repository URL.

    Returns:
        list[str]: List of tag strings (deduplicated, without ^{} suffixes).

    Raises:
        FetchError: If the git command fails.
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

    Args:
        version_list (list[str]): Raw version strings (may include 'v' prefix).
        include_prerelease (bool): If True, include pre-release and dev versions.

    Returns:
        list[tuple[str, Version]]: Sorted list of (original_string, parsed_Version) tuples, ascending.
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

    Args:
        versions (dict[str, str | None]): Dict mapping version string to requires_python (or None).
        min_python (Version | None): Minimum Python version the project supports, or None to skip filtering.

    Returns:
        list[str]: List of compatible version strings.
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

    Args:
        versions (dict[str, str | None]): Mapping of version string to requires_python (or None).
        min_python (Version | None): Minimum Python version to filter against.

    Returns:
        str | None: The latest version string, or None if none found.
    """
    compatible = filter_python_compatible(versions, min_python)
    sorted_versions = clean_and_sort_versions(compatible)
    if not sorted_versions:
        sorted_versions = clean_and_sort_versions(compatible, include_prerelease=True)

    if not sorted_versions:
        return None

    return str(sorted_versions[-1][1])


def find_tag_for_version(git_tags: list[str], version: str) -> str | None:
    """Find the git tag whose normalized version equals *version*.

    Used to translate a ``uv``-resolved version back into the tag a pre-commit ``rev`` must carry, preserving
    whatever prefix style the upstream repo uses (``1.2.3`` vs ``v1.2.3``).

    Args:
        git_tags (list[str]): Tag strings from git ls-remote.
        version (str): Normalized version string to match.

    Returns:
        str | None: The original tag string, or None if no tag matches.
    """
    for orig_tag, parsed in clean_and_sort_versions(git_tags, include_prerelease=True):
        if str(parsed) == version:
            return orig_tag

    return None


def find_highest_common_version(
    pypi_versions: dict[str, str | None],
    git_tags: list[str],
    *,
    min_python: Version | None = None,
) -> tuple[str, str] | None:
    """Find the highest version present in both PyPI releases and git tags.

    Args:
        pypi_versions (dict[str, str | None]): Dict mapping version string to requires_python.
        git_tags (list[str]): Tag strings from git ls-remote.
        min_python (Version | None): Minimum Python version to filter against.

    Returns:
        tuple[str, str] | None: Tuple of (git_tag_string, normalized_version) for the highest common stable
            version, or None if no overlap.
    """
    compatible = filter_python_compatible(pypi_versions, min_python)
    pypi_sorted = clean_and_sort_versions(compatible)
    git_sorted = clean_and_sort_versions(git_tags)

    pypi_set = {str(parsed) for _, parsed in pypi_sorted}

    for orig_tag, parsed_tag in reversed(git_sorted):
        if str(parsed_tag) in pypi_set:
            return orig_tag, str(parsed_tag)

    return None

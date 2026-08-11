# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Remote pre-commit hook definition fetching."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import requests
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from shared.http_client import get_session
from shared.pip_config import PipConfig, resolve_verify

from precommit.config import FETCH_HOOKS_TIMEOUT
from precommit.exceptions import FetchError

logger = logging.getLogger(__name__)


def _build_raw_url(repo_url: str, rev: str) -> str:
    """Build a raw content URL for .pre-commit-hooks.yaml.

    Args:
        repo_url (str): Repository URL.
        rev (str): Git revision.

    Returns:
        str: URL to the raw .pre-commit-hooks.yaml file.

    Raises:
        FetchError: If the repository host is not supported.
    """
    normalized = repo_url.removesuffix(".git")
    hostname = urlparse(normalized).hostname or ""

    if hostname == "github.com" or hostname.endswith(".github.com"):
        raw_base = normalized.replace(hostname, "raw.githubusercontent.com", 1)
        return f"{raw_base}/{rev}/.pre-commit-hooks.yaml"

    if hostname == "gitlab.com" or hostname.endswith(".gitlab.com"):
        return f"{normalized}/-/raw/{rev}/.pre-commit-hooks.yaml"

    msg = f"Unsupported repository host: {repo_url}"
    raise FetchError(msg)


def _parse_hooks_yaml(
    content: bytes,
    raw_url: str,
    response_text: str,
) -> list[dict[str, Any]]:
    """Parse YAML hook definitions from raw response content.

    Args:
        content (bytes): Raw response body bytes.
        raw_url (str): URL the content was fetched from (used in error messages).
        response_text (str): Response text preview (used in error messages).

    Returns:
        list[dict[str, Any]]: Parsed list of hook definition dicts.

    Raises:
        FetchError: If the YAML is unparseable or not a list.
    """
    try:
        hooks = YAML().load(content)
    except YAMLError as exc:
        msg = f"YAML parse error for {raw_url}:\n{response_text[:500]}"
        raise FetchError(msg) from exc

    if not isinstance(hooks, list):
        msg = f"Expected list of hooks from {raw_url}, got {type(hooks).__name__}"
        raise FetchError(msg)

    return hooks


def fetch_hooks(
    repo_url: str,
    rev: str,
    *,
    pip_config: PipConfig | None = None,
) -> list[dict[str, Any]]:
    """Fetch .pre-commit-hooks.yaml from a remote repository.

    Constructs the raw content URL for GitHub or GitLab and downloads the hook definition file.

    Args:
        repo_url (str): Repository URL (GitHub or GitLab).
        rev (str): Git revision (tag or commit hash).
        pip_config (PipConfig | None): Optional pip configuration for SSL settings.

    Returns:
        list[dict[str, Any]]: List of hook definition dicts parsed from the YAML.

    Raises:
        FetchError: If the URL cannot be determined, the request fails, or the YAML is unparseable.
    """
    raw_url = _build_raw_url(repo_url, rev)
    logger.debug("Fetching hooks from %s", raw_url)

    session = get_session()
    try:
        # verify may be False for pip trusted-host entries — intentional, mirrors pip semantics
        resp = session.get(
            url=raw_url,
            timeout=FETCH_HOOKS_TIMEOUT,
            verify=resolve_verify(raw_url, pip_config),
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        msg = f"Failed to fetch hooks from {raw_url}: {exc}"
        raise FetchError(msg) from exc

    hooks = _parse_hooks_yaml(resp.content, raw_url, resp.text)

    logger.debug("Fetched %d hook definitions from %s", len(hooks), repo_url)
    return hooks

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Detect pins held below their newest release by another dependency.

Some pins cannot be raised to the newest release because a sibling caps them. ``python-semantic-release``
requires ``rich~=14.0`` and ``tomlkit~=0.13.0``, so ``rich==15.0.0`` or ``tomlkit==0.15.1`` makes the project
unsatisfiable — ``uv lock`` refuses it outright.

``syncdeps`` already avoids proposing such a pin, because it takes whatever ``uv`` resolved. Dependabot has no
such protection: it compares a pin against the index in isolation, opens a PR for the newest release, and that
PR can never merge. Worse, a Dependabot PR touching only ``pyproject.toml`` matches every workflow's
``paths-ignore``, so almost no checks run and the PR looks green while being unmergeable.

This module identifies those capped pins so the Dependabot ignore list can suppress exactly them.

The suppression is deliberately narrow. An ignore rule also applies to Dependabot *security* updates, so
ignoring a package that is not actually capped would hide a future security bump for no benefit. A pin is
therefore reported only when the newest release is genuinely higher than the version ``uv`` chose, which is
precisely the case where a Dependabot proposal could not be installed anyway.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from packaging.version import InvalidVersion, Version
from shared.concurrency import PARALLEL_WORKERS

from depsync.exceptions import FetchError
from depsync.fetchers import fetch_pypi_versions, resolve_latest_version

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from packaging.version import Version as VersionType
    from shared.pip_config import PipConfig

logger = logging.getLogger(__name__)


def _is_capped(resolved: str, latest: str | None) -> bool:
    """Report whether *latest* is a real release above *resolved*.

    Args:
        resolved (str): Version ``uv`` chose for the package.
        latest (str | None): Newest release found on the index, or None.

    Returns:
        bool: True when the index offers something strictly newer than the resolution. Unparsable versions
            return False, so an odd version string can never manufacture a suppression.

    """
    if latest is None:
        return False

    try:
        return Version(latest) > Version(resolved)
    except InvalidVersion:
        logger.debug("Cannot compare %s against %s; not treating as capped", latest, resolved)
        return False


def detect_capped_pins(
    packages: Iterable[str],
    resolved: Mapping[str, str],
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
    min_python: VersionType | None = None,
) -> dict[str, str]:
    """Find pins that ``uv`` resolved below the newest release available.

    Args:
        packages (Iterable[str]): Managed package names to examine.
        resolved (Mapping[str, str]): Package name to the version ``uv`` resolved.
        index_url (str | None): Optional PEP 503 index URL to query first.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs.
        pip_config (PipConfig | None): Pip configuration for SSL settings.
        min_python (VersionType | None): Minimum Python version, so a release that dropped support for it is
            not mistaken for an available upgrade.

    Returns:
        dict[str, str]: Package name to its resolved version, for packages the index offers a newer release
            of. A fetch failure omits the package rather than guessing.

    """
    names = [name for name in packages if name in resolved]
    if not names:
        return {}

    def _latest_for(name: str) -> str | None:
        try:
            versions = fetch_pypi_versions(
                name,
                index_url=index_url,
                extra_index_urls=extra_index_urls,
                pip_config=pip_config,
            )
        except FetchError:
            logger.debug("Cannot fetch versions for %s; skipping cap check", name)
            return None

        return resolve_latest_version(versions, min_python)

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        latest_by_name = list(pool.map(_latest_for, names))

    capped = {
        name: resolved[name]
        for name, latest in zip(names, latest_by_name, strict=True)
        if _is_capped(resolved[name], latest)
    }

    for name, version in sorted(capped.items()):
        logger.info("%s is capped at %s by another dependency", name, version)

    return capped

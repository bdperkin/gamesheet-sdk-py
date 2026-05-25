"""gamesheet_sdk — unofficial Python SDK for the GameSheet Inc. platform."""

from __future__ import annotations

try:
    from ._version import __version__
except ImportError:  # pragma: no cover - fallback only fires uninstalled
    # _version.py is written by hatch-vcs at build time; when running from
    # a source tree that hasn't been built (or an editable install that
    # predates the latest git tag), fall back to installed metadata.
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("gamesheet-sdk-py")
    except PackageNotFoundError:
        __version__ = "0+unknown"

__all__ = ["__version__"]

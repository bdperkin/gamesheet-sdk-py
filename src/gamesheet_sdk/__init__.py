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

from .associations import Association, list_associations
from .auth import load_access_token, login
from .browser import BrowserSession
from .config import Config
from .exceptions import AuthenticationError, GameSheetError
from .session import Session

__all__ = [
    "Association",
    "AuthenticationError",
    "BrowserSession",
    "Config",
    "GameSheetError",
    "Session",
    "__version__",
    "list_associations",
    "load_access_token",
    "login",
]

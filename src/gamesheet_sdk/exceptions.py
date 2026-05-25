"""Exceptions raised by gamesheet_sdk.

The hierarchy is intentionally small: a single base class so callers can
``except GameSheetError`` to catch anything this SDK raises. More specific
subclasses will be added as concrete failure modes appear.
"""

from __future__ import annotations


class GameSheetError(Exception):
    """Base class for every exception raised by ``gamesheet_sdk``."""

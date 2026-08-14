# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Exceptions raised by gamesheet_sdk.

The hierarchy is intentionally small: a single base class so callers can ``except GameSheetError`` to catch
anything this SDK raises. More specific subclasses will be added as concrete failure modes appear.
"""

from __future__ import annotations


class GameSheetError(Exception):
    """Base class for every exception raised by ``gamesheet_sdk``."""


class AuthenticationError(GameSheetError):
    """Raised when authentication against the GameSheet WebUI fails.

    Covers both missing/incomplete credentials and active server-side rejection (the submit form does not
    redirect off the sign-in page within the allotted timeout).
    """


class GameSheetAPIError(GameSheetError):
    """Raised when the GameSheet API returns an HTTP 4xx/5xx error status code.

    Args:
        message (str): Context message for error reporting.
        status_code (int): The HTTP response status code (e.g. 404, 500).
        endpoint (str): The API endpoint path that triggered the error.
        response_body (str | None): Truncated response body text from the server.

    """

    def __init__(
        self: GameSheetAPIError,
        message: str,
        status_code: int,
        endpoint: str,
        response_body: str | None = None,
    ) -> None:
        """Initialize GameSheetAPIError.

        Args:
            message (str): Context message for error reporting.
            status_code (int): The HTTP response status code.
            endpoint (str): The API endpoint path.
            response_body (str | None): Truncated response body text.

        """
        # Every argument is forwarded to ``super().__init__()`` (and kept positional) so the default
        # ``BaseException.__reduce__`` round-trips the instance through ``pickle``/``copy.copy()``.
        super().__init__(message, status_code, endpoint, response_body)
        self.status_code = status_code
        self.endpoint = endpoint
        self.response_body = response_body

    def __str__(self: GameSheetAPIError) -> str:
        """Return just the context message, not the whole ``args`` tuple.

        Returns:
            str: The context message passed to the constructor.

        """
        return str(self.args[0])


class GameSheetNotFoundError(GameSheetAPIError):
    """Raised when a requested resource is not found (HTTP 404)."""


class GameSheetPermissionError(AuthenticationError, GameSheetAPIError):
    """Raised when access to a resource is forbidden (HTTP 403)."""


class GameSheetRateLimitError(GameSheetAPIError):
    """Raised when the client is rate-limited (HTTP 429)."""


class GameSheetValidationError(GameSheetError):
    """Raised when client-side parameter validation fails."""

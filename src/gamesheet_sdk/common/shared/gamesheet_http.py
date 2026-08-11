# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""HTTP response handling utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.common import errors
from gamesheet_sdk.common.exceptions import (
    AuthenticationError,
    GameSheetAPIError,
    GameSheetError,
    GameSheetNotFoundError,
    GameSheetPermissionError,
    GameSheetRateLimitError,
)

if TYPE_CHECKING:
    import requests


def handle_response(
    response: requests.Response,
    endpoint: str,
    context_msg: str = "request",
) -> None:
    """Centralized HTTP error handling for all domain modules.

    Args:
        response (requests.Response): The HTTP response object.
        endpoint (str): The endpoint that was called.
        context_msg (str): Context message for error reporting (e.g., ``"GET associations"``).

    Raises:
        AuthenticationError: If response status is 401 (Unauthorized).
        GameSheetPermissionError: If response status is 403 (Forbidden).
        GameSheetNotFoundError: If response status is 404 (Not Found).
        GameSheetRateLimitError: If response status is 429 (Too Many Requests).
        GameSheetAPIError: For any other >= 400 response status.
    """
    text_val = getattr(response, "text", "")
    body_snippet = text_val[:200] if isinstance(text_val, str) and text_val else None

    if response.status_code == 401:
        msg = errors.ERROR_MSG_401_GENERIC.format(context=context_msg)
        raise AuthenticationError(msg)

    if response.status_code == 403:
        msg = errors.ERROR_MSG_403_GENERIC.format(context=context_msg)
        raise GameSheetPermissionError(
            msg,
            status_code=403,
            endpoint=endpoint,
            response_body=body_snippet,
        )

    if response.status_code == 404:
        msg = errors.ERROR_MSG_404_RESOURCE.format(endpoint=endpoint)
        raise GameSheetNotFoundError(
            msg,
            status_code=404,
            endpoint=endpoint,
            response_body=body_snippet,
        )

    if response.status_code == 429:
        msg = f"Rate limit exceeded (HTTP 429) for {endpoint}"
        raise GameSheetRateLimitError(
            msg,
            status_code=429,
            endpoint=endpoint,
            response_body=body_snippet,
        )

    if response.status_code >= 400:
        msg = errors.ERROR_MSG_GENERIC_HTTP.format(
            context=context_msg.upper(),
            endpoint=endpoint,
            status_code=response.status_code,
            text=response.text,
        )
        raise GameSheetAPIError(
            msg,
            status_code=response.status_code,
            endpoint=endpoint,
            response_body=body_snippet,
        )


def check_bff_response_status(data: dict[str, Any], _endpoint: str) -> None:
    """Validate BFF API response status field.

    BFF API responses include a ``"status"`` field that should be ``"success"``.

    Args:
        data (dict[str, Any]): The parsed JSON response data.

    Raises:
        GameSheetError: If status is not ``"success"``.
    """
    status = data.get("status")
    if status != "success":
        msg = errors.ERROR_MSG_BFF_NON_SUCCESS.format(status=status, response=data)
        raise GameSheetError(msg)


def handle_season_scoped_response(
    response: requests.Response,
    endpoint: str,
    season_id: str,
    method: str = "GET",
    resource_type: str = "season",
) -> None:
    """Handle HTTP errors for season-scoped API calls.

    Provides season-specific error messages for common failures.

    Args:
        response (requests.Response): The HTTP response object.
        endpoint (str): The endpoint that was called.
        season_id (str): The season ID used in the request.
        method (str): The HTTP verb (GET, POST, PATCH, DELETE).
        resource_type (str): Type of resource being accessed (e.g. "season", "referee").

    Raises:
        AuthenticationError: If response status is 401 (Unauthorized).
        GameSheetPermissionError: If response status is 403 (Forbidden).
        GameSheetNotFoundError: If response status is 404 (Not Found).
        GameSheetAPIError: For any other >= 400 response status.
    """
    text_val = getattr(response, "text", "")
    body_snippet = repr(text_val[:200]) if isinstance(text_val, str) and text_val else None

    if response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if response.status_code == 403:
        msg = errors.ERROR_MSG_403_GENERIC.format(context=f"{method} {resource_type}")
        raise GameSheetPermissionError(
            msg,
            status_code=403,
            endpoint=endpoint,
            response_body=body_snippet,
        )

    if response.status_code == 404:
        msg = errors.ERROR_MSG_404_SEASON.format(season_id=season_id)
        raise GameSheetNotFoundError(
            msg,
            status_code=404,
            endpoint=endpoint,
            response_body=body_snippet,
        )

    if response.status_code >= 400:
        msg = errors.ERROR_MSG_GENERIC_HTTP.format(
            context=method.upper(),
            endpoint=endpoint,
            status_code=response.status_code,
            text=repr(text_val[:200]) if isinstance(text_val, str) else "",
        )
        raise GameSheetAPIError(
            msg,
            status_code=response.status_code,
            endpoint=endpoint,
            response_body=body_snippet,
        )

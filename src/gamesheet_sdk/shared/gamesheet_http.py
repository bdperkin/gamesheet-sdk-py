"""HTTP response handling utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    import requests


def handle_response(
    response: requests.Response,
    endpoint: str,
    context_msg: str = "request",
) -> None:
    """Centralized HTTP error handling for all domain modules.

    Args:
        response: The HTTP response object
        endpoint: The endpoint that was called
        context_msg: Context message for error reporting (e.g., "GET associations")

    Raises:
        AuthenticationError: If response status is 401 (Unauthorized)
        GameSheetError: If response status is 404 or any other >= 400
    """
    if response.status_code == 401:
        msg = (
            f"Access token rejected (HTTP 401) for {context_msg}. "
            "Use `gamesheet-sdk-py login` to authenticate."
        )
        raise AuthenticationError(msg)
    if response.status_code == 404:
        msg = f"Resource not found (HTTP 404) for {endpoint}"
        raise GameSheetError(msg)
    if response.status_code >= 400:
        msg = f"{context_msg.upper()} {endpoint} returned HTTP {response.status_code}: {response.text}"
        raise GameSheetError(msg)


def check_bff_response_status(data: dict[str, Any], endpoint: str) -> None:
    """Validate BFF API response status field.

    BFF API responses include a "status" field that should be "success".

    Args:
        data: The parsed JSON response data
        endpoint: The endpoint that was called

    Raises:
        GameSheetError: If status is not "success"
    """
    status = data.get("status")
    if status != "success":
        msg = f"{endpoint} returned non-success status: {status}"
        raise GameSheetError(msg)

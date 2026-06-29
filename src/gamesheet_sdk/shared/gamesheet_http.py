# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""HTTP response handling utilities."""

from __future__ import annotations

from typing import Any

import requests

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError


def handle_response(
    response: requests.Response,
    endpoint: str,
    context_msg: str = "request",
) -> None:
    """Centralized HTTP error handling for all domain modules.

    :param response: The HTTP response object.
    :type response: requests.Response
    :param endpoint: The endpoint that was called.
    :type endpoint: str
    :param context_msg: Context message for error reporting (e.g., ``"GET associations"``).
    :type context_msg: str
    :raises AuthenticationError: If response status is 401 (Unauthorized).
    :raises GameSheetError: If response status is 404 or any other >= 400.
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

    BFF API responses include a ``"status"`` field that should be ``"success"``.

    :param data: The parsed JSON response data.
    :type data: dict[str, Any]
    :param endpoint: The endpoint that was called.
    :type endpoint: str
    :raises GameSheetError: If status is not ``"success"``.
    """
    status = data.get("status")
    if status != "success":
        msg = f"{endpoint} returned non-success status: {status}"
        raise GameSheetError(msg)


def handle_season_scoped_response(
    response: requests.Response,
    endpoint: str,
    season_id: str,
) -> None:
    """Handle HTTP errors for season-scoped API calls.

    Provides season-specific error messages for common failures.

    :param response: The HTTP response object.
    :type response: requests.Response
    :param endpoint: The endpoint that was called.
    :type endpoint: str
    :param season_id: The season ID used in the request.
    :type season_id: str
    :raises AuthenticationError: If response status is 401 (Unauthorized).
    :raises GameSheetError: If response status is 404 or any other >= 400.
    """
    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Season '{season_id}' not found (HTTP 404). "
            f"Make sure you're using a valid season ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)

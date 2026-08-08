# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""HTTP response handling utilities."""

from __future__ import annotations

from typing import Any

import requests

from gamesheet_sdk.common import errors
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError


def handle_response(
    response: requests.Response,
    endpoint: str,
    context_msg: str = "request",
) -> None:
    """Centralized HTTP error handling for all domain modules.

    Args:
        response (requests.Response): The HTTP response object.
        endpoint (str): The endpoint that was called.
        context_msg (str): Context message for error reporting (e.g.,
            ``"GET associations"``).

    Raises:
        AuthenticationError: If response status is 401 (Unauthorized) or
            403 (Forbidden).
        GameSheetError: If response status is 404 or any other >= 400.
    """
    if response.status_code == 401:
        msg = errors.ERROR_MSG_401_GENERIC.format(context=context_msg)
        raise AuthenticationError(msg)

    if response.status_code == 403:
        msg = errors.ERROR_MSG_403_GENERIC.format(context=context_msg)
        raise AuthenticationError(msg)

    if response.status_code == 404:
        msg = errors.ERROR_MSG_404_RESOURCE.format(endpoint=endpoint)
        raise GameSheetError(msg)

    if response.status_code >= 400:
        msg = errors.ERROR_MSG_GENERIC_HTTP.format(
            context=context_msg.upper(),
            endpoint=endpoint,
            status_code=response.status_code,
            text=response.text,
        )
        raise GameSheetError(msg)


# pylint: disable-next=unused-argument
def check_bff_response_status(data: dict[str, Any], endpoint: str) -> None:  # noqa: U100
    """Validate BFF API response status field.

    BFF API responses include a ``"status"`` field that should be ``"success"``.

    Args:
        data (dict[str, Any]): The parsed JSON response data.
        endpoint (str): The endpoint that was called.

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
) -> None:
    """Handle HTTP errors for season-scoped API calls.

    Provides season-specific error messages for common failures.

    Args:
        response (requests.Response): The HTTP response object.
        endpoint (str): The endpoint that was called.
        season_id (str): The season ID used in the request.

    Raises:
        AuthenticationError: If response status is 401 (Unauthorized).
        GameSheetError: If response status is 404 or any other >= 400.
    """
    if response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if response.status_code == 404:
        msg = errors.ERROR_MSG_404_SEASON.format(season_id=season_id)
        raise GameSheetError(msg)

    if response.status_code >= 400:
        msg = errors.ERROR_MSG_GENERIC_HTTP.format(
            context="GET",
            endpoint=endpoint,
            status_code=response.status_code,
            text=repr(response.text[:200]),
        )
        raise GameSheetError(msg)

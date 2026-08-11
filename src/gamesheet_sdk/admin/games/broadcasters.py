# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Broadcaster operations for games."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.admin.games.models import Broadcaster
from gamesheet_sdk.common.constants import BFF_API_BASE_URL, BFF_BROADCASTERS
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.shared import check_bff_response_status, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


def list_broadcasters(session: Session) -> list[Broadcaster]:
    """Return the list of valid broadcasters.

    Fetches the current list of broadcaster services from the BFF API. The returned broadcaster keys can be
    used when creating or updating scheduled games.

    Args:
        session (Session): An authenticated :class:`Session`.

    Returns:
        list[Broadcaster]: A list of :class:`Broadcaster` objects.

    Raises:
        AuthenticationError: If the server returns 401 or 403.
        GameSheetError: For any other non-2xx response.
    """
    url = f"{BFF_API_BASE_URL}{BFF_BROADCASTERS}"
    response = session.get(url)
    handle_response(response, url, "GET broadcasters")
    body: dict[str, Any] = response.json()
    check_bff_response_status(body, url)
    broadcasters_data = body.get("data", [])
    return [Broadcaster(**b) for b in broadcasters_data]


def validate_broadcaster_key(session: Session, broadcaster: str) -> str:
    """Validate a broadcaster key and return the correctly-cased version.

    Fetches the list of valid broadcasters and performs a case-insensitive match. Returns the broadcaster key
    with the correct casing as stored in the API.

    Args:
        session (Session): An authenticated :class:`Session`.
        broadcaster (str): The broadcaster key to validate (case- insensitive).

    Returns:
        str: The correctly-cased broadcaster key.

    Raises:
        GameSheetError: If the broadcaster key is not valid.
    """
    if not broadcaster:
        return broadcaster

    broadcasters = list_broadcasters(session)
    broadcaster_lower = broadcaster.lower()
    for b in broadcasters:
        if b.key.lower() == broadcaster_lower:
            return b.key

    valid_keys = [b.key for b in broadcasters]
    joined_valid_keys = ", ".join(valid_keys)
    msg = f"Invalid broadcaster '{broadcaster}'. Valid options (case-insensitive): {joined_valid_keys}"
    raise GameSheetError(msg)

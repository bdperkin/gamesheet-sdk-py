# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet iPad keys: Scoring Access Keys for season scoring via iPad app.

iPad Keys (also called Scoring Access Keys or API Keys) are credentials used by the GameSheet iPad app for
live game scoring. Each key is associated with one or more seasons and grants read/write access to scoring
data within those seasons. This module talks to the GameSheet JSON:API at ``/api/api-
keys?filter[season]={season_id}`` directly with the lightweight :class:`gamesheet_sdk.Session` path -- no
Playwright needed for read-only access once a bearer token has been obtained (typically by reading the SPA's
``accessToken`` from the saved browser storage state via :func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.session import Session

_ENDPOINT = "/api/api-keys"
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class IPadKey(BaseModel):
    """A single iPad / Scoring Access Key.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/api-keys?filter[season]={id}`` to a flat
    typed model.
    """

    id: str = Field(description="API key identifier (string in JSON:API).")
    value: str = Field(description="The actual key value (e.g., 'ipad-ncrr-kw').")
    description: str = Field(description="Human-readable description of the key.")
    roles: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of role objects defining access levels.",
    )
    live_scoring_scopes: list[str] = Field(
        default_factory=list,
        description="Scopes granted for live scoring (e.g., ['read', 'write']).",
    )
    created_at: datetime = Field(description="When the key was created.")
    updated_at: datetime = Field(description="Last time the key was updated.")


def _parse(item: dict[str, Any]) -> IPadKey:
    """Flatten a JSON:API resource object into an :class:`IPadKey`."""
    attrs = item.get("attributes", {})
    return IPadKey(
        id=item["id"],
        **attrs,
    )


def list_ipad_keys(session: Session, season_id: str) -> list[IPadKey]:
    """Return every iPad / Scoring Access Key for the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose iPad keys to list.
    :type season_id: str
    :returns: A list of :class:`IPadKey`, in the order the server returned them. The list may be empty if the
        season has no iPad keys configured.
    :rtype: list[IPadKey]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    response = session.get(
        _ENDPOINT,
        params={"filter[season]": season_id},
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )
    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"No iPad keys found or invalid season ID '{season_id}' (HTTP 404). "
            f"Make sure you're using a valid season ID, not a league ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {_ENDPOINT} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return [_parse(item) for item in body.get("data", [])]

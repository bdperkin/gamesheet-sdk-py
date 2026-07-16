# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Public lookup data from the teams API.

The ``GET /api/lookups`` endpoint is unauthenticated and returns every enumeration category used by the teams
dashboard (sports, positions, game types, countries, etc.).  Each category is a list of values sharing at
least a ``key`` field; additional fields vary by category.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
import requests

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.teams.shared.constants import TEAMS_API_GATEWAY, TEAMS_LOOKUPS_PATH


class LookupValue(BaseModel):
    """A single value within a lookup category.

    All lookup values carry a ``key``.  Most also have a ``title``; the few that don't (e.g. entitlements)
    default to ``""``.  Category-specific fields (``abbr``, ``url``, ``sport``, ``scopes``, etc.) are
    preserved via ``extra="allow"`` and appear in :meth:`model_dump` output.

    :var key: Machine-readable identifier.
    :var title: Human-readable display name.
    """

    model_config = ConfigDict(extra="allow")

    key: str = Field(description="Machine-readable identifier.")
    title: str = Field(default="", description="Human-readable display name.")


def list_lookups(
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, list[LookupValue]]:
    """Fetch all lookup categories from the teams API.

    This is a public endpoint — no authentication is required.

    :param timeout: HTTP request timeout in seconds.
    :type timeout: float
    :returns: Dictionary mapping category names to lists of :class:`LookupValue` objects.
    :rtype: dict[str, list[LookupValue]]
    :raises GameSheetError: If the server returns a non-2xx status code.
    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_LOOKUPS_PATH}"
    response = requests.get(url, timeout=timeout)
    if response.status_code >= 400:
        msg = f"GET {TEAMS_LOOKUPS_PATH} returned HTTP {response.status_code}: {response.text}"
        raise GameSheetError(msg)
    data: dict[str, list[dict[str, Any]]] = response.json().get("data", {})
    return {category: [LookupValue(**item) for item in values] for category, values in data.items()}

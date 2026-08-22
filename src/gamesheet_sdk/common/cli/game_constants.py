# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Help text shared by the unified game option set.

These strings are duplicated from :mod:`gamesheet_sdk.admin.cli.constants` rather than imported, so the
``common`` pillar does not take a dependency on ``admin``.
"""

from __future__ import annotations

from typing import Final

FLEXIBLE_DATETIME_HELP: Final[str] = (
    "Flexible date/time format (e.g., '2026-07-04 7:00pm', "
    "'July 4 2026 19:00', '2026-07-04T19:00:00-04:00'). "
    "If no timezone is specified, the system timezone is used."
)
SPLIT_DATE_HELP: Final[str] = "Date component (e.g., '2026-07-04', 'July 4 2026')."
SPLIT_TIME_HELP: Final[str] = "Time component (e.g., '7:00pm', '19:00')."
DURATION_HELP: Final[str] = (
    "Game duration. Bare numbers are minutes (e.g., '75'); suffixed forms are also accepted "
    "(e.g., '1h15m', '90m', '1.5h', '1:15')."
)
IANA_TIMEZONE_HELP_TEXT: Final[str] = "IANA time zone name (e.g., America/New_York)"
TIMEZONE_OFFSET_HELP_TEXT: Final[str] = "Time zone offset in minutes (e.g., -240 for EDT)"
GAME_TYPE_HELP: Final[str] = "Game type. Valid: exhibition, playoff, regular_season, tournament."
LOCATION_HELP: Final[str] = (
    "Game location/venue. Format: '<location_name> <surface_name>' (case-insensitive). "
    "Validated against the API by `gamesheet-admin`."
)
BROADCASTER_HELP: Final[str] = (
    "Broadcast provider key (case-insensitive, e.g., LIVEBARN). "
    "Validated against the API by `gamesheet-admin`."
)

#: Suffix appended to the help of options only one backend can actually send.
ADMIN_ONLY_SUFFIX: Final[str] = "Ignored with a warning by `gamesheet-teams`."
TEAMS_ONLY_SUFFIX: Final[str] = "Ignored with a warning by `gamesheet-admin`."

__all__ = [
    "ADMIN_ONLY_SUFFIX",
    "BROADCASTER_HELP",
    "DURATION_HELP",
    "FLEXIBLE_DATETIME_HELP",
    "GAME_TYPE_HELP",
    "IANA_TIMEZONE_HELP_TEXT",
    "LOCATION_HELP",
    "SPLIT_DATE_HELP",
    "SPLIT_TIME_HELP",
    "TEAMS_ONLY_SUFFIX",
    "TIMEZONE_OFFSET_HELP_TEXT",
]

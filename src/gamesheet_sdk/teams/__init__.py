# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams dashboard SDK for GameSheet."""

from gamesheet_sdk.teams.login import TeamsLoginFlow, refresh_access_token
from gamesheet_sdk.teams.lookups import LookupValue, list_lookups
from gamesheet_sdk.teams.seasons import (
    PenaltyCode,
    SeasonDetail,
    SeasonSummary,
    SeasonTeam,
    fetch_seasons_raw,
    get_season,
    get_season_penalty_codes,
    get_season_teams,
    list_seasons,
)
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.teams import (
    TeamDetail,
    TeamSummary,
    fetch_team_raw,
    fetch_teams_raw,
    get_team,
    list_teams,
    update_team,
    upload_team_image,
)

__all__ = [
    "LookupValue",
    "PenaltyCode",
    "SeasonDetail",
    "SeasonSummary",
    "SeasonTeam",
    "TeamDetail",
    "TeamSummary",
    "TeamsAuthenticatedSession",
    "TeamsLoginFlow",
    "fetch_seasons_raw",
    "fetch_team_raw",
    "fetch_teams_raw",
    "get_season",
    "get_season_penalty_codes",
    "get_season_teams",
    "get_team",
    "list_lookups",
    "list_seasons",
    "list_teams",
    "refresh_access_token",
    "update_team",
    "upload_team_image",
]

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet roster: players and coaches within a season.

Roster data represents the people associated with teams in a season - both players and coaches. This module
provides access to:

- **Players** — player roster operations
- **Coaches** — coach roster operations

Each view talks to the GameSheet JSON:API at ``/api/seasons/{season_id}/players`` and
``/api/seasons/{season_id}/coaches`` directly with the lightweight :class:`gamesheet_sdk.Session` path -- no
Playwright needed for read-only access once a bearer token has been obtained.
"""

from gamesheet_sdk.admin.roster.coaches import (
    assign_coach,
    assign_team_coach,
    create_coach,
    create_team_coach,
    delete_coach,
    delete_team_coach,
    get_coach,
    get_coach_penalty_report,
    get_team_coach,
    list_coaches,
    list_team_coaches,
    unassign_coach,
    unassign_team_coach,
    update_coach,
    update_team_coach,
)
from gamesheet_sdk.admin.roster.models import Coach, Player
from gamesheet_sdk.admin.roster.players import (
    assign_player,
    create_player,
    delete_player,
    get_player,
    get_player_penalty_report,
    list_players,
    unassign_player,
    update_player,
)
from gamesheet_sdk.admin.roster.team_players import (
    assign_team_player,
    create_team_player,
    delete_team_player,
    get_team_player,
    list_team_players,
    unassign_team_player,
    update_team_player,
)

__all__ = [
    "Coach",
    "Player",
    "assign_coach",
    "assign_player",
    "assign_team_coach",
    "assign_team_player",
    "create_coach",
    "create_player",
    "create_team_coach",
    "create_team_player",
    "delete_coach",
    "delete_player",
    "delete_team_coach",
    "delete_team_player",
    "get_coach",
    "get_coach_penalty_report",
    "get_player",
    "get_player_penalty_report",
    "get_team_coach",
    "get_team_player",
    "list_coaches",
    "list_players",
    "list_team_coaches",
    "list_team_players",
    "unassign_coach",
    "unassign_player",
    "unassign_team_coach",
    "unassign_team_player",
    "update_coach",
    "update_player",
    "update_team_coach",
    "update_team_player",
]

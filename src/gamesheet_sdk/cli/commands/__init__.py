# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI command modules."""

from __future__ import annotations

from gamesheet_sdk.cli.commands.associations import associations_group
from gamesheet_sdk.cli.commands.completion import completion_command
from gamesheet_sdk.cli.commands.divisions import divisions_group, divisions_teams_group
from gamesheet_sdk.cli.commands.games import games_group
from gamesheet_sdk.cli.commands.ipad_keys import ipad_keys_group
from gamesheet_sdk.cli.commands.leagues import leagues_group
from gamesheet_sdk.cli.commands.locations import locations_group
from gamesheet_sdk.cli.commands.login import login_command
from gamesheet_sdk.cli.commands.referees import referees_group
from gamesheet_sdk.cli.commands.roster import roster_group
from gamesheet_sdk.cli.commands.roster_coaches import coaches_group
from gamesheet_sdk.cli.commands.roster_players import players_group
from gamesheet_sdk.cli.commands.seasons import seasons_group
from gamesheet_sdk.cli.commands.teams import teams_group
from gamesheet_sdk.cli.commands.teams_roster import (
    register_teams_roster_group,
    teams_roster_group,
)
from gamesheet_sdk.cli.commands.teams_roster_coaches import teams_roster_coaches_group
from gamesheet_sdk.cli.commands.teams_roster_players import teams_roster_players_group

__all__ = [
    "associations_group",
    "coaches_group",
    "completion_command",
    "divisions_group",
    "divisions_teams_group",
    "games_group",
    "ipad_keys_group",
    "leagues_group",
    "locations_group",
    "login_command",
    "players_group",
    "referees_group",
    "register_teams_roster_group",
    "roster_group",
    "seasons_group",
    "teams_group",
    "teams_roster_coaches_group",
    "teams_roster_group",
    "teams_roster_players_group",
]

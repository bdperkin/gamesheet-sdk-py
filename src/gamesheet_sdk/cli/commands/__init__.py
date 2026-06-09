"""CLI command modules."""

from __future__ import annotations

from gamesheet_sdk.cli.commands.associations import associations_group
from gamesheet_sdk.cli.commands.completion import completion_command
from gamesheet_sdk.cli.commands.divisions import divisions_group
from gamesheet_sdk.cli.commands.games import games_group
from gamesheet_sdk.cli.commands.ipad_keys import ipad_keys_group
from gamesheet_sdk.cli.commands.leagues import leagues_group
from gamesheet_sdk.cli.commands.login import login_command
from gamesheet_sdk.cli.commands.referees import referees_group
from gamesheet_sdk.cli.commands.roster import roster_group
from gamesheet_sdk.cli.commands.seasons import seasons_group
from gamesheet_sdk.cli.commands.teams import teams_group

__all__ = [
    "associations_group",
    "completion_command",
    "divisions_group",
    "games_group",
    "ipad_keys_group",
    "leagues_group",
    "login_command",
    "referees_group",
    "roster_group",
    "seasons_group",
    "teams_group",
]

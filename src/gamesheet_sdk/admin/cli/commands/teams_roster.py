# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams roster command group - player and coach management for teams."""

from __future__ import annotations

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.cli.commands.teams_roster_coaches import (
    teams_roster_coaches_group,
)
from gamesheet_sdk.admin.cli.commands.teams_roster_players import (
    teams_roster_players_group,
)
from gamesheet_sdk.common.cli.core import ResourceGroup


# Teams roster nested group
@click.group(
    "roster",
    cls=ResourceGroup,
    default="players",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to manage roster for.",
)
@click.option(
    "--team-id",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to manage roster for.",
)
@click.pass_context
def teams_roster_group(ctx: Context, season_id: str, team_id: str) -> None:
    """Manage roster (players and coaches) for a specific team.

    Invoking ``roster`` with no sub-command runs ``players`` by default. The --season-id and --team-id options
    are required and apply to all sub-commands.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param team_id: The team identifier
    :type team_id: str
    """
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id, "team_id": team_id}


def register_teams_roster_group(teams_group: click.Group) -> None:
    """Register the teams roster sub-group with the teams group.

    :param teams_group: The main teams group to attach roster commands to.
    :type teams_group: click.Group
    """
    teams_group.add_command(teams_roster_group)


# Register player and coach groups from separate modules
teams_roster_group.add_command(teams_roster_players_group)
teams_roster_group.add_command(teams_roster_coaches_group)

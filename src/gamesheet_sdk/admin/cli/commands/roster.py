# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Roster command group with nested sub-commands."""

from __future__ import annotations

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.cli.commands.roster_coaches import coaches_group
from gamesheet_sdk.admin.cli.commands.roster_players import players_group
from gamesheet_sdk.common.cli.core import ResourceGroup


@click.group(
    "roster",
    cls=ResourceGroup,
    default="players",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
        "assign": ("register", "enlist", "place"),
        "unassign": ("drop", "release", "deregister"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to manage roster for.",
)
@click.pass_context
def roster_group(ctx: Context, season_id: str) -> None:
    r"""Manage roster (players and coaches) within a season.

    Invoking ``roster`` with no sub-command runs ``players`` by default. The --season-id option is required
    and applies to all sub-commands.\f

    Args:
        ctx (Context): Click context object containing config
        season_id (str): The season identifier
    """
    # Store season_id in context for sub-commands to access
    # ctx.obj is a Config object from the root CLI - wrap it in a dict
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id}


# Register player and coach groups from separate modules
roster_group.add_command(players_group)
roster_group.add_command(coaches_group)

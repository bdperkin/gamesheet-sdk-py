# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Games command group with nested sub-commands."""

from __future__ import annotations

import rich_click as click
from rich_click import Context

from gamesheet_sdk.cli.commands.games_brackets import brackets_group
from gamesheet_sdk.cli.commands.games_completed import completed_group
from gamesheet_sdk.cli.commands.games_scheduled import scheduled_group
from gamesheet_sdk.cli.core import ResourceGroup


@click.group(
    "games",
    cls=ResourceGroup,
    default="scheduled",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID for games.",
)
@click.pass_context
def games_group(ctx: Context, season_id: str) -> None:
    """Manage games (scheduled, completed, brackets) within a season.

    Invoking ``games`` with no sub-command runs ``scheduled`` by default.
    The --season-id option is required and applies to all sub-commands.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    """
    # Store season_id in context for sub-commands to access
    # ctx.obj is a Config object from the root CLI - wrap it in a dict
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id}


# Register sub-groups from separate modules
games_group.add_command(scheduled_group)
games_group.add_command(completed_group)
games_group.add_command(brackets_group)

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Games command group with nested sub-commands."""

from __future__ import annotations

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.cli.commands.games_brackets import brackets_group
from gamesheet_sdk.admin.cli.commands.games_completed import completed_group
from gamesheet_sdk.admin.cli.commands.games_scheduled import scheduled_group
from gamesheet_sdk.common.cli.core import ResourceGroup

#: Verbs promoted from ``games scheduled`` to ``games``, so the admin command path lines up with
#: ``gamesheet-teams schedule games <verb>``.
SCHEDULED_VERBS = ("create", "get", "list", "update", "delete")


@click.group(
    "games",
    cls=ResourceGroup,
    default="scheduled",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("del", "rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    default=None,
    help="Season ID for games. May also be given on the sub-command.",
)
@click.pass_context
def games_group(ctx: Context, season_id: str | None) -> None:
    r"""Manage games (scheduled, completed, brackets) within a season.

    Invoking ``games`` with no sub-command runs ``scheduled`` by default, and the ``scheduled`` verbs are also
    reachable directly as ``games create``, ``games list``, and so on. A season is required, but may be given
    either here or on the sub-command, so both ``games --season-id 1 create`` and ``games create --season-id
    1`` work.\f

    Args:
        ctx (Context): Click context object containing config
        season_id (str | None): The season identifier, if given at this level

    """
    # Store season_id in context for sub-commands to access
    # ctx.obj is a Config object from the root CLI - wrap it in a dict
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id}


# Register sub-groups from separate modules
games_group.add_command(scheduled_group)
games_group.add_command(completed_group)
games_group.add_command(brackets_group)

# Promote the scheduled verbs to the group itself.
for _verb in SCHEDULED_VERBS:
    _command = scheduled_group.commands[_verb]
    games_group.add_command(_command, _verb)

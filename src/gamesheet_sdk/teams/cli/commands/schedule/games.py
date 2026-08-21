# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Scheduled games CLI commands for GameSheet teams.

Every verb here declares the unified game option set from :mod:`gamesheet_sdk.common.cli.game_options`, the
same set ``gamesheet-admin games`` declares, so a command line written for either CLI runs unchanged on the
other. Execution lives in :mod:`gamesheet_sdk.teams.cli.commands.schedule.game_runner`.
"""

from __future__ import annotations

from typing import Any

import rich_click as click
from rich_click import Context

from gamesheet_sdk.common.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.common.cli.decorators import (
    columns_option,
    common_output_options,
)
from gamesheet_sdk.common.cli.game_options import (
    game_detail_options,
    game_id_option,
    game_side_options,
    game_time_options,
    season_id_option,
)
from gamesheet_sdk.common.cli.teams_lookup_options import (
    availability_options,
    list_filter_options,
)
from gamesheet_sdk.teams.cli.commands.schedule import game_runner


@click.group(
    "games",
    cls=ResourceGroup,
    default="list",
    aliases={
        "create": ("add", "new"),
        "delete": ("del", "rm", "remove"),
        "get": ("show", "view"),
        "list": ("ls",),
        "update": ("set", "edit"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def games_group() -> None:
    """Manage scheduled games.

    Invoking ``games`` with no sub-command runs ``list`` by default.
    """


@games_group.command(
    "create",
    aliases=("add", "new"),
)
@season_id_option(required=True)
@game_time_options
@game_side_options
@game_detail_options(required=True)
@common_output_options
@columns_option
@click.pass_context
def games_create_command(ctx: Context, **params: Any) -> None:
    r"""Create a new scheduled game.

    Provide any two of ``--start-datetime`` (or ``--start-date`` + ``--start-time``), ``--end-datetime`` (or
    ``--end-date`` + ``--end-time``), and ``--duration`` to automatically calculate the third. The
    association and league are derived from ``--season-id``.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_create(ctx, params)


@games_group.command("list")
@list_filter_options(team_required=True)
@season_id_option(required=False)
@common_output_options
@columns_option
@click.pass_context
def games_list_command(ctx: Context, **params: Any) -> None:
    r"""List scheduled games for a team.

    Selected via ``--team-id`` / ``-t`` or the ``GAMESHEET_TEAM_ID`` environment variable.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_list(ctx, params)


@games_group.command("get")
@game_id_option
@season_id_option(required=False)
@availability_options()
@common_output_options
@columns_option
@click.pass_context
def games_get_command(ctx: Context, **params: Any) -> None:
    r"""Show details for a scheduled game.

    Selected via ``--game-id`` / ``-g`` / ``--id`` or ``GAMESHEET_GAME_ID``.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_get(ctx, params)


@games_group.command(
    "delete",
    aliases=("del", "rm", "remove"),
)
@game_id_option
@season_id_option(required=False)
@common_output_options
@columns_option
@confirm_destructive("this scheduled game")
@click.pass_context
def games_delete_command(ctx: Context, **params: Any) -> None:
    r"""Delete a scheduled game.

    Selected via ``--game-id`` / ``-g`` / ``--id`` or ``GAMESHEET_GAME_ID``. This operation is destructive and
    requires confirmation unless --force is specified.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_delete(ctx, params)


@games_group.command(
    "update",
    aliases=("set", "edit"),
)
@game_id_option
@season_id_option(required=False)
@game_time_options
@game_side_options
@game_detail_options(required=False)
@common_output_options
@columns_option
@click.pass_context
def games_update_command(ctx: Context, **params: Any) -> None:
    r"""Update a scheduled game.

    Selected via ``--game-id`` / ``-g`` / ``--id`` or ``GAMESHEET_GAME_ID``. Only specified fields are
    updated; unspecified fields retain their current values.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_update(ctx, params)


__all__ = [
    "games_create_command",
    "games_delete_command",
    "games_get_command",
    "games_group",
    "games_list_command",
    "games_update_command",
]

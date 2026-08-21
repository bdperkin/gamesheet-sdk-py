# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Scheduled games CLI commands.

Every verb here declares the unified game option set from :mod:`gamesheet_sdk.common.cli.game_options`, the
same set ``gamesheet-teams schedule games`` declares, so a command line written for either CLI runs unchanged
on the other. Execution lives in :mod:`gamesheet_sdk.admin.cli.shared.game_runner`.
"""

from __future__ import annotations

from typing import Any

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.cli.shared import game_runner
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


@click.group(
    "scheduled",
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
def scheduled_group() -> None:
    """Manage scheduled games.

    Invoking ``scheduled`` with no sub-command runs ``list`` by default.
    """


@scheduled_group.command("get")
@game_id_option
@season_id_option(required=False)
@availability_options(ignored=True)
@common_output_options
@columns_option
@click.pass_context
def scheduled_get_command(ctx: Context, **params: Any) -> None:
    r"""Get detailed information about a scheduled game.

    Uses the JSON:API /api/seasons/{id}/schedule/{game_id} endpoint for richer structured data.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_get(ctx, params)


@scheduled_group.command("list")
@season_id_option(required=False)
@list_filter_options(team_required=False, ignored=True)
@common_output_options
@columns_option
@click.pass_context
def scheduled_list_command(ctx: Context, **params: Any) -> None:
    r"""List all scheduled games in the specified season.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_list(ctx, params)


@scheduled_group.command("create")
@season_id_option(required=False)
@game_time_options
@game_side_options
@game_detail_options(required=True)
@common_output_options
@columns_option
@click.pass_context
def scheduled_create_command(ctx: Context, **params: Any) -> None:
    r"""Create a new scheduled game.

    Requires authentication (run 'gamesheet-admin login' first). Provide any two of ``--start-datetime`` (or
    ``--start-date`` + ``--start-time``), ``--end-datetime`` (or ``--end-date`` + ``--end-time``), and
    ``--duration`` to automatically calculate the third. If time zone options are not specified, they default
    to the local system timezone.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_create(ctx, params)


@scheduled_group.command("update")
@game_id_option
@season_id_option(required=False)
@game_time_options
@game_side_options
@game_detail_options(required=False)
@common_output_options
@columns_option
@click.pass_context
def scheduled_update_command(ctx: Context, **params: Any) -> None:
    r"""Update a scheduled game.

    Requires authentication (run 'gamesheet-admin login' first). Only specified fields are updated;
    unspecified fields retain their current values. You may provide any combination of ``--start-datetime``
    (or ``--start-date`` + ``--start-time``), ``--end-datetime`` (or ``--end-date`` + ``--end-time``), and
    ``--duration`` to automatically calculate missing time fields.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_update(ctx, params)


@scheduled_group.command("delete")
@game_id_option
@season_id_option(required=False)
@common_output_options
@columns_option
@confirm_destructive("this scheduled game")
@click.pass_context
def scheduled_delete_command(ctx: Context, **params: Any) -> None:
    r"""Delete a scheduled game.

    Requires authentication (run 'gamesheet-admin login' first). This operation is destructive and requires
    confirmation unless --force is specified.\f

    Args:
        ctx (Context): Click context object containing config.
        **params (Any): The unified game option set, as declared by the decorators above.

    """
    game_runner.run_delete(ctx, params)


__all__ = [
    "scheduled_create_command",
    "scheduled_delete_command",
    "scheduled_get_command",
    "scheduled_group",
    "scheduled_list_command",
    "scheduled_update_command",
]

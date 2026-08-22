# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Seasons command for the GameSheet teams dashboard.

Provides commands to list and view seasons, penalty codes, and assigned teams.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from rich_click import Context

from gamesheet_sdk.common.cli.core import ResourceGroup
from gamesheet_sdk.common.cli.decorators import (
    columns_option,
    common_output_options,
)
from gamesheet_sdk.common.cli.rendering import (
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.seasons import (
    get_season as _get_season_action,
)
from gamesheet_sdk.teams.seasons import (
    get_season_penalty_codes as _get_season_penalty_codes_action,
)
from gamesheet_sdk.teams.seasons import (
    get_season_teams as _get_season_teams_action,
)
from gamesheet_sdk.teams.seasons import (
    list_seasons as _list_seasons_action,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


@click.group(
    "seasons",
    cls=ResourceGroup,
    default="list",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "penalty-codes": ("penalty_codes", "penalties"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def seasons_group() -> None:
    """View seasons, penalty codes, and teams from the teams API.

    Invoking ``seasons`` with no sub-command runs ``list`` by default.
    """


@seasons_group.command("list")
@common_output_options
@columns_option
@click.pass_context
def seasons_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all seasons available to the authenticated user.

    Focuses on association ID/title, season ID, league ID/title, stats year, and season title.\f

    Args:
        ctx (Context): Click context object containing config.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    seasons = run_action_or_exit(
        session,
        _list_seasons_action,
        timeout=config.timeout,
    )
    render_list_command(seasons, output_format, output_path, columns_spec)


@seasons_group.command("get")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to retrieve details for.",
)
@common_output_options
@columns_option
@click.pass_context
def seasons_get_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""Get detailed metadata for a specific season.

    Retrieves season details excluding penaltyCodes and teams.\f

    Args:
        ctx (Context): Click context object containing config.
        season_id (str): Season identifier.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    season = run_action_or_exit(
        session,
        _get_season_action,
        season_id,
        timeout=config.timeout,
    )
    render_get_command(season, output_format, output_path, columns_spec)


@seasons_group.command("penalty-codes")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to retrieve penalty codes for.",
)
@common_output_options
@columns_option
@click.pass_context
def seasons_penalty_codes_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all penalty codes configured for a specific season.

    Retrieves all penalty code definitions and rules for the season.\f

    Args:
        ctx (Context): Click context object containing config.
        season_id (str): Season identifier.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    penalty_codes = run_action_or_exit(
        session,
        _get_season_penalty_codes_action,
        season_id,
        timeout=config.timeout,
    )
    render_list_command(penalty_codes, output_format, output_path, columns_spec)


@seasons_group.command("teams")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to retrieve teams for.",
)
@common_output_options
@columns_option
@click.pass_context
def seasons_teams_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all teams participating in a specific season.

    Retrieves all team records associated with the season.\f

    Args:
        ctx (Context): Click context object containing config.
        season_id (str): Season identifier.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    teams = run_action_or_exit(
        session,
        _get_season_teams_action,
        season_id,
        timeout=config.timeout,
    )
    render_list_command(teams, output_format, output_path, columns_spec)

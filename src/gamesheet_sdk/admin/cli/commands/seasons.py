# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Seasons command group."""

from __future__ import annotations

import rich_click as click
from rich_click import Choice, Context

from gamesheet_sdk.admin.cli.constants import SEASON_STATUS
from gamesheet_sdk.admin.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.admin.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.admin.seasons import (
    get_season as _get_season_action,
    list_seasons as _list_seasons_action,
)
from gamesheet_sdk.common.cli.core import ResourceGroup
from gamesheet_sdk.common.config import Config


@click.group(
    "seasons",
    cls=ResourceGroup,
    default="list",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def seasons_group() -> None:
    """Manage seasons within a league.

    Invoking ``seasons`` with no sub-command runs ``list`` by default.
    """


@seasons_group.command("list")
@click.option(
    "--league-id",
    type=str,
    envvar="GAMESHEET_LEAGUE_ID",
    required=True,
    help="League ID to list seasons for.",
)
@click.option(
    "--starts-after",
    type=str,
    default=None,
    help="Filter seasons starting after this date (ISO format: YYYY-MM-DD).",
)
@click.option(
    "--ends-before",
    type=str,
    default=None,
    help="Filter seasons ending before this date (ISO format: YYYY-MM-DD).",
)
@click.option(
    "--status",
    type=Choice(SEASON_STATUS, case_sensitive=False),
    default=None,
    help="Filter by season status.",
)
@click.option(
    "--stats-year",
    type=str,
    default=None,
    help="Filter by statistics year (e.g., '2026-2027').",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="Filter by season title (free-form text search).",
)
@common_output_options
@list_columns_option
@click.pass_context
def seasons_list_command(
    ctx: Context,
    league_id: str,
    *,
    starts_after: str | None,
    ends_before: str | None,
    status: str | None,
    stats_year: str | None,
    title: str | None,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List the seasons in the specified league.

    The league ID can be provided via --league-id or the GAMESHEET_LEAGUE_ID environment variable. Requires a
    saved session from `gamesheet-admin login` -- the bearer token is read out of the browser storage state
    on disk and attached to the HTTP request. No browser is launched.

    Optional filters can be applied to narrow the results:
    --starts-after, --ends-before, --status, --stats-year, and --title.\f

    :param ctx: Click context object containing config
    :type ctx: Context
    :param league_id: The league identifier
    :type league_id: str
    :param starts_after: Optional filter for seasons starting after this date
    :type starts_after: str | None
    :param ends_before: Optional filter for seasons ending before this date
    :type ends_before: str | None
    :param status: Optional filter for season status
    :type status: str | None
    :param stats_year: Optional filter for statistics year
    :type stats_year: str | None
    :param title: Optional filter for season title
    :type title: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :param columns_spec: Optional comma-separated list of columns to display
    :type columns_spec: str | None
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    seasons = run_action_or_exit(
        session,
        lambda s: _list_seasons_action(
            s,
            league_id,
            starts_after=starts_after,
            ends_before=ends_before,
            status=status,
            stats_year=stats_year,
            title=title,
        ),
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
@get_fields_option
@click.pass_context
def seasons_get_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific season.

    The season ID can be provided via --season-id or the GAMESHEET_SEASON_ID environment variable. Requires a
    saved session from `gamesheet-admin login` -- the bearer token is read out of the browser storage state on
    disk and attached to the HTTP request. No browser is launched. The output displays season metadata as key-
    value pairs, with each field on its own row. Complex nested fields (like settings, flagging_criteria) are
    displayed as JSON.\f

    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :param fields_spec: Optional comma-separated list of fields to display
    :type fields_spec: str | None
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    season = run_action_or_exit(session, _get_season_action, season_id)
    render_get_command(season, output_format, output_path, fields_spec)

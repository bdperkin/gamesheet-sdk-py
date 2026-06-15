"""Divisions command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.divisions import create_division as _create_division_action
from gamesheet_sdk.divisions import delete_division as _delete_division_action
from gamesheet_sdk.divisions import list_division_teams as _list_division_teams_action
from gamesheet_sdk.divisions import list_divisions as _list_divisions_action
from gamesheet_sdk.divisions import update_division as _update_division_action
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output

if TYPE_CHECKING:
    from gamesheet_sdk.auth.session import AuthenticatedSession
    from gamesheet_sdk.divisions import Division


@click.group(
    "divisions",
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
def divisions_group() -> None:
    """Manage divisions within a season.

    Invoking ``divisions`` with no sub-command runs ``list`` by default.
    """


@divisions_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list divisions for.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all columns the API returns)."),
)
@click.pass_context
def divisions_list_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all divisions in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)

    def _list_with_counts(sess: AuthenticatedSession, sid: str) -> list[Division]:
        return _list_divisions_action(sess, sid, include_team_counts=True)

    divisions = run_action_or_exit(session, _list_with_counts, season_id)
    rows = [division.model_dump(mode="json") for division in divisions]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


@divisions_group.command("create")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID in which to create the division.",
)
@click.option(
    "--title",
    type=str,
    required=True,
    help="Division name/title.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="Optional external identifier for integration with third-party systems.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
# pylint: disable-next=too-many-positional-arguments
def divisions_create_command(
    ctx: Context,
    season_id: str,
    title: str,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new division in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)

    def _create_with_kwargs(sess: AuthenticatedSession, sid: str, div_title: str) -> Division:
        return _create_division_action(sess, sid, div_title, external_id=external_id)

    division = run_action_or_exit(session, _create_with_kwargs, season_id, title)
    rows = [division.model_dump(mode="json")]
    rendered = render(rows, fmt=output_format)
    write_output(rendered, output_path, fmt=output_format)
    if output_path is None:
        click.secho(f"\nDivision '{division.title}' created successfully (ID: {division.id})", fg="green")


@divisions_group.command("update")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the division.",
)
@click.option(
    "--division-id",
    type=str,
    required=True,
    help="Division ID to update.",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="New division name/title.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="New external identifier.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
# pylint: disable-next=too-many-positional-arguments
def divisions_update_command(
    ctx: Context,
    season_id: str,
    division_id: str,
    title: str | None,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update an existing division.

    At least one of --title or --external-id must be provided. Requires authentication (run 'gamesheet-sdk-py
    login' first).
    """
    if title is None is external_id:
        click.secho("Error: At least one of --title or --external-id must be provided.", fg="red", err=True)
        raise Exit(1)

    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)

    def _update_with_kwargs(sess: AuthenticatedSession, sid: str, div_id: str) -> Division:
        return _update_division_action(sess, sid, div_id, title=title, external_id=external_id)

    division = run_action_or_exit(session, _update_with_kwargs, season_id, division_id)
    rows = [division.model_dump(mode="json")]
    rendered = render(rows, fmt=output_format)
    write_output(rendered, output_path, fmt=output_format)
    if output_path is None:
        click.secho(f"\nDivision '{division.title}' updated successfully (ID: {division.id})", fg="green")


@divisions_group.command("teams")
@click.option(
    "--division-id",
    type=str,
    required=True,
    help="Division ID to list teams for.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all columns the API returns)."),
)
@click.pass_context
def divisions_teams_command(
    ctx: Context,
    division_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all teams in the specified division.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    teams = run_action_or_exit(session, _list_division_teams_action, division_id)
    rows = [team.model_dump(mode="json") for team in teams]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


@divisions_group.command("delete")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the division.",
)
@click.option(
    "--division-id",
    type=str,
    required=True,
    help="Division ID to delete.",
)
@confirm_destructive("division")
@click.pass_context
def divisions_delete_command(
    ctx: Context,
    season_id: str,
    division_id: str,
) -> None:
    """Delete a division.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    run_action_or_exit(session, _delete_division_action, season_id, division_id)
    click.secho(f"Division {division_id} deleted successfully.", fg="green")

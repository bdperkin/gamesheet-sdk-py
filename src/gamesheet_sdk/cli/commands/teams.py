"""Teams command group."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output
from gamesheet_sdk.teams import Team
from gamesheet_sdk.teams import create_team as _create_team_action
from gamesheet_sdk.teams import delete_team as _delete_team_action
from gamesheet_sdk.teams import list_teams as _list_teams_action
from gamesheet_sdk.teams import update_team as _update_team_action

if TYPE_CHECKING:
    from gamesheet_sdk.auth.session import AuthenticatedSession


@click.group(
    "teams",
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
def teams_group() -> None:
    """Manage teams within a season.

    Invoking ``teams`` with no sub-command runs ``list`` by default.
    """


@teams_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list teams for.",
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
def teams_list_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all teams in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    teams = run_action_or_exit(session, _list_teams_action, season_id)
    rows = [team.model_dump(mode="json") for team in teams]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


@teams_group.command("create")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to create the team in.",
)
@click.option(
    "--title",
    type=str,
    required=True,
    help="Team name/title.",
)
@click.option(
    "--division-id",
    type=str,
    required=True,
    help="Division ID the team belongs to.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="Optional external identifier for the team.",
)
@click.option(
    "--logo",
    "logo_path",
    type=Path(exists=True, dir_okay=False, readable=True),
    default=None,
    help="Optional path to a local logo image file.",
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
# pylint: disable-next=too-many-positional-arguments,too-many-locals
def teams_create_command(
    ctx: Context,
    season_id: str,
    title: str,
    division_id: str,
    external_id: str | None,
    logo_path: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new team in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)

    def _create_with_kwargs(sess: AuthenticatedSession) -> dict[str, Any]:
        return _create_team_action(
            sess,
            season_id,
            title,
            division_id,
            external_id=external_id,
            logo_path=logo_path,
        )

    result = run_action_or_exit(session, _create_with_kwargs)
    # For tabular formats, convert to a list of key-value rows
    if output_format not in ("json", "yaml"):
        rows = [{"field": k, "value": v} for k, v in result.items()]
        rendered = render(rows, fmt=output_format, columns=None)
    else:
        # For data formats, output the whole object
        rendered = render([result], fmt=output_format, columns=None)
    write_output(rendered, output_path, fmt=output_format)

    # Show success message (consistent with divisions create)
    if output_path is None:
        team_title = result.get("prototeam", {}).get("title", title)
        team_id = result.get("seasonTeam", {}).get("id", "unknown")
        click.secho(f"\nTeam '{team_title}' created successfully (ID: {team_id})", fg="green")


@teams_group.command("update")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the team.",
)
@click.option(
    "--team-id",
    type=str,
    required=True,
    help="Team ID to update.",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="New team name/title.",
)
@click.option(
    "--division-id",
    type=str,
    default=None,
    help="New division ID.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="New external identifier.",
)
@click.option(
    "--logo",
    "logo_path",
    type=Path(exists=True, dir_okay=False, readable=True),
    default=None,
    help="Path to a new logo image file.",
)
@click.option(
    "--remove-logo",
    is_flag=True,
    default=False,
    help="Remove the team's logo.",
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
def teams_update_command(
    ctx: Context,
    season_id: str,
    team_id: str,
    title: str | None,
    division_id: str | None,
    external_id: str | None,
    logo_path: str | None,
    *,
    remove_logo: bool,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update an existing team.

    Requires authentication (run 'gamesheet-sdk-py login' first). At least one field must be provided for
    update.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)

    def _update_with_kwargs(sess: AuthenticatedSession) -> Team:
        return _update_team_action(
            sess,
            season_id,
            team_id,
            title=title,
            division_id=division_id,
            external_id=external_id,
            logo_path=logo_path,
            remove_logo=remove_logo,
        )

    team = run_action_or_exit(session, _update_with_kwargs)
    rendered = render([team.model_dump(mode="json")], fmt=output_format, columns=None)
    write_output(rendered, output_path, fmt=output_format)


@teams_group.command("delete")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the team.",
)
@click.option(
    "--team-id",
    type=str,
    required=True,
    help="Team ID to delete.",
)
@click.pass_context
def teams_delete_command(
    ctx: Context,
    season_id: str,
    team_id: str,
) -> None:
    """Delete a team.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    run_action_or_exit(session, _delete_team_action, season_id, team_id)
    click.secho(f"Team {team_id} deleted successfully.", fg="green")

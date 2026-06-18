"""Divisions command group."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from click.exceptions import Exit
from rich_click import Path

from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.divisions import create_division as _create_division_action
from gamesheet_sdk.divisions import delete_division as _delete_division_action
from gamesheet_sdk.divisions import get_division as _get_division_action
from gamesheet_sdk.divisions import list_division_teams as _list_division_teams_action
from gamesheet_sdk.divisions import list_divisions as _list_divisions_action
from gamesheet_sdk.divisions import update_division as _update_division_action

if TYPE_CHECKING:
    from rich_click import Context

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


@divisions_group.command("get")
@click.option(
    "--division-id",
    type=str,
    envvar="GAMESHEET_DIVISION_ID",
    required=True,
    help="Division ID to retrieve details for.",
)
@common_output_options
@get_fields_option
@click.pass_context
def divisions_get_command(
    ctx: Context,
    division_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific division.

    The division ID can be provided via --division-id or the GAMESHEET_DIVISION_ID environment variable.
    Requires a saved session from `gamesheet-sdk-py login`. The output displays division metadata as key-value
    pairs, with each field on its own row.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    division = run_action_or_exit(session, _get_division_action, division_id)
    render_get_command(division, output_format, output_path, fields_spec)


@divisions_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list divisions for.",
)
@common_output_options
@list_columns_option
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
    render_list_command(divisions, output_format, output_path, columns_spec)


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
@common_output_options
@click.pass_context
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

    def _create_with_kwargs(
        sess: AuthenticatedSession,
        sid: str,
        div_title: str,
    ) -> Division:
        return _create_division_action(sess, sid, div_title, external_id=external_id)

    division = run_action_or_exit(session, _create_with_kwargs, season_id, title)
    render_list_command([division], output_format, output_path)
    if output_path is None:
        click.secho(
            f"\nDivision '{division.title}' created successfully (ID: {division.id})",
            fg="green",
        )


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
@common_output_options
@click.pass_context
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
        click.secho(
            "Error: At least one of --title or --external-id must be provided.",
            fg="red",
            err=True,
        )
        raise Exit(1)
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)

    def _update_with_kwargs(
        sess: AuthenticatedSession,
        sid: str,
        div_id: str,
    ) -> Division:
        return _update_division_action(
            sess,
            sid,
            div_id,
            title=title,
            external_id=external_id,
        )

    division = run_action_or_exit(session, _update_with_kwargs, season_id, division_id)
    render_list_command([division], output_format, output_path)
    if output_path is None:
        click.secho(
            f"\nDivision '{division.title}' updated successfully (ID: {division.id})",
            fg="green",
        )


@divisions_group.group(
    "teams",
    cls=ResourceGroup,
    default="list",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def divisions_teams_group() -> None:
    """Manage teams within a division.

    Invoking ``teams`` with no sub-command runs ``list`` by default.
    """


@divisions_teams_group.command("list")
@click.option(
    "--division-id",
    type=str,
    envvar="GAMESHEET_DIVISION_ID",
    required=True,
    help="Division ID to list teams for.",
)
@common_output_options
@list_columns_option
@click.pass_context
def divisions_teams_list_command(
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
    render_list_command(teams, output_format, output_path, columns_spec)


@divisions_teams_group.command("get")
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
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to retrieve.",
)
@common_output_options
@click.pass_context
def divisions_teams_get_command(
    ctx: Context,
    season_id: str,
    team_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get detailed information about a specific team.

    Delegates to teams get functionality.
    """
    # pylint: disable-next=import-outside-toplevel
    from gamesheet_sdk.teams import get_team as _get_team_action

    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    item = run_action_or_exit(session, _get_team_action, season_id, team_id)
    render_get_command(item, output_format, output_path)


@divisions_teams_group.command("create")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to create the team in.",
)
@click.option(
    "--division-id",
    type=str,
    envvar="GAMESHEET_DIVISION_ID",
    required=True,
    help="Division ID the team belongs to.",
)
@click.option(
    "--title",
    type=str,
    required=True,
    help="Team name/title.",
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
    type=Path(exists=True, dir_okay=False),
    help="Optional path to a local logo image file.",
)
@common_output_options
@click.pass_context
def divisions_teams_create_command(
    ctx: Context,
    season_id: str,
    division_id: str,
    title: str,
    external_id: str | None,
    logo_path: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new team in the specified division.

    Delegates to teams create functionality.
    """
    # pylint: disable-next=import-outside-toplevel
    from gamesheet_sdk.teams import create_team as _create_team_action

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
    render_get_command(result, output_format, output_path)
    if output_path is None:
        team_title = result.get("prototeam", {}).get("title", title)
        team_id = result.get("seasonTeam", {}).get("id", "unknown")
        click.secho(
            f"\nTeam '{team_title}' created successfully (ID: {team_id})",
            fg="green",
        )


@divisions_teams_group.command("update")
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
    envvar="GAMESHEET_TEAM_ID",
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
    type=Path(exists=True, dir_okay=False),
    help="Path to a new logo image file.",
)
@click.option(
    "--remove-logo",
    is_flag=True,
    default=False,
    help="Remove the team's logo.",
)
@common_output_options
@click.pass_context
def divisions_teams_update_command(
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

    Delegates to teams update functionality.
    """
    from gamesheet_sdk.teams import Team
    from gamesheet_sdk.teams import update_team as _update_team_action

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
    render_list_command([team], output_format, output_path)


@divisions_teams_group.command("delete")
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
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to delete.",
)
@confirm_destructive("team")
@click.pass_context
def divisions_teams_delete_command(
    ctx: Context,
    season_id: str,
    team_id: str,
) -> None:
    """Delete a team.

    Delegates to teams delete functionality.
    """
    # pylint: disable-next=import-outside-toplevel
    from gamesheet_sdk.teams import delete_team as _delete_team_action

    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    run_action_or_exit(session, _delete_team_action, season_id, team_id)
    click.secho(f"Team {team_id} deleted successfully.", fg="green")


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

"""CLI helper functions shared across commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.auth.session import AuthenticatedSession
from gamesheet_sdk.auth.tokens import load_access_token, load_refresh_token, save_tokens
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from rich_click import Context

    from gamesheet_sdk.config import Config


def build_authenticated_session(
    __ctx: Context,  # noqa: U101
    config: Config,
) -> AuthenticatedSession:
    """Build an AuthenticatedSession from saved tokens.

    :param config: The application config.
    :returns: An AuthenticatedSession ready to use.
    :raises Exit: If no tokens are saved.
    """
    access = load_access_token(config)
    refresh = load_refresh_token(config)
    if access is None or refresh is None:
        click.secho(
            "No saved session found. Run `gamesheet-sdk-py login` first.",
            fg="red",
            err=True,
        )
        raise Exit(1)
    return AuthenticatedSession(
        config,
        access_token=access,
        refresh_token=refresh,
        on_refresh=lambda tokens: save_tokens(config, **tokens),
    )


def run_action_or_exit(session: AuthenticatedSession, action: Any, *args: Any) -> Any:
    """Run an action function with error handling.

    Wraps the action call in the session's context manager and catches :exc:`AuthenticationError` and
    :exc:`GameSheetError`. On either exception, prints a user-friendly error message to stderr and exits with
    code 1. The session context manager ensures proper cleanup (e.g., closing connections) regardless of
    success or failure.
    :param session: The authenticated session to use as a context manager.
    :param action: A callable that takes ``session`` and ``*args`` and returns a result. Typically a domain
        action function (e.g., ``list_associations``, ``list_leagues``).
    :param args: Positional arguments passed to ``action`` after ``session``.
    :returns: The result of ``action(session, *args)`` on success.
    :raises Exit: If ``action`` raises :exc:`AuthenticationError` or :exc:`GameSheetError`. Exit code is 1 in
        both cases.
    """
    try:
        with session:
            return action(session, *args)
    except AuthenticationError as exc:
        click.secho(f"Authentication required: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    except GameSheetError as exc:
        click.secho(f"GameSheet error: {exc}", fg="red", err=True)
        raise Exit(1) from exc


def run_team_update(
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
    """Run team update action and render output.

    Shared implementation for teams update and divisions teams update commands.

    :param ctx: The click context containing the config.
    :param season_id: Season ID containing the team.
    :param team_id: Team ID to update.
    :param title: New team name/title.
    :param division_id: New division ID.
    :param external_id: New external identifier.
    :param logo_path: Path to a new logo image file.
    :param remove_logo: Remove the team's logo.
    :param output_format: Output format for rendering.
    :param output_path: Optional output file path.
    :raises Exit: If no fields are provided for update.
    """
    from gamesheet_sdk.teams import Team
    from gamesheet_sdk.teams import update_team as _update_team_action

    # Validate that at least one field is provided for update
    if all(v is None or v is False for v in (title, division_id, external_id, logo_path, remove_logo)):
        click.secho(
            "Error: At least one field must be provided for update. Use --title, --division-id, "
            "--external-id, --logo-path, or --remove-logo.",
            fg="red",
            err=True,
        )
        raise Exit(1)

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
    from gamesheet_sdk.cli.shared import render_list_command

    render_list_command([team], output_format, output_path)


def run_team_create(
    ctx: Context,
    season_id: str,
    title: str,
    division_id: str,
    external_id: str | None,
    logo_path: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Run team create action and render output with success message.

    Shared implementation for teams create and divisions teams create commands.

    :param ctx: The click context containing the config.
    :param season_id: Season ID to create the team in.
    :param title: Team name/title.
    :param division_id: Division ID the team belongs to.
    :param external_id: Optional external identifier.
    :param logo_path: Optional path to a logo image file.
    :param output_format: Output format for rendering.
    :param output_path: Optional output file path.
    """
    from gamesheet_sdk.teams import create_team as _create_team_action

    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)

    def _create_with_kwargs(sess: AuthenticatedSession) -> Any:
        return _create_team_action(
            sess,
            season_id,
            title,
            division_id,
            external_id=external_id,
            logo_path=logo_path,
        )

    result = run_action_or_exit(session, _create_with_kwargs)
    from gamesheet_sdk.cli.shared import render_get_command

    render_get_command(result, output_format, output_path)
    # Show success message when output goes to stdout
    if output_path is None:
        team_title = result.get("prototeam", {}).get("title", title)
        team_id = result.get("seasonTeam", {}).get("id", "unknown")
        click.secho(
            f"\nTeam '{team_title}' created successfully (ID: {team_id})",
            fg="green",
        )


def run_roster_assign_with_output(
    action: Any,
    session: AuthenticatedSession,
    resource_type: str,
    resource_id: str,
    target_id: str,
    output_format: str,
    output_path: str | None,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Run roster assign action with error handling and output rendering.

    :param action: The assign action function to call.
    :param session: Authenticated session.
    :param resource_type: Type of resource being assigned (player/coach).
    :param resource_id: ID of the resource being assigned.
    :param target_id: ID of the target team.
    :param output_format: Output format for rendering.
    :param output_path: Optional output file path.
    :param args: Positional arguments to pass to the action.
    :param kwargs: Keyword arguments to pass to the action.
    :raises Exit: If the action raises an exception.
    """
    from gamesheet_sdk.cli.shared import render_get_command

    try:
        with session:
            result = action(*args, **kwargs)
    except Exception as exc:
        click.secho(f"Error assigning {resource_type}: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    render_get_command(result, output_format, output_path, None)
    click.secho(
        f"{resource_type.capitalize()} {resource_id} assigned to team {target_id} successfully.",
        fg="green",
    )


def run_roster_unassign(
    action: Any,
    session: AuthenticatedSession,
    resource_type: str,
    resource_id: str,
    target_id: str,
    *args: Any,
) -> None:
    """Run roster unassign action with error handling.

    :param action: The unassign action function to call.
    :param session: Authenticated session.
    :param resource_type: Type of resource being unassigned (player/coach).
    :param resource_id: ID of the resource being unassigned.
    :param target_id: ID of the target team.
    :param args: Additional arguments to pass to the action.
    :raises Exit: If the action raises an exception.
    """
    try:
        with session:
            action(*args)
    except Exception as exc:
        click.secho(f"Error unassigning {resource_type}: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    click.secho(
        f"{resource_type.capitalize()} {resource_id} unassigned from team {target_id} successfully.",
        fg="green",
    )

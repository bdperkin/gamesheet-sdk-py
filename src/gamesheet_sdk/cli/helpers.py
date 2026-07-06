# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT
# pylint: disable=missing-param-doc

"""CLI helper functions shared across commands."""

from __future__ import annotations

from typing import Any

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

from gamesheet_sdk import errors
from gamesheet_sdk.auth.session import AuthenticatedSession
from gamesheet_sdk.auth.tokens import load_access_token, load_refresh_token, save_tokens
from gamesheet_sdk.config import Config
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError


def build_authenticated_session(
    config: Config,
) -> AuthenticatedSession:
    """Build an AuthenticatedSession from saved tokens.

    :param config: The application config.
    :type config: Config
    :returns: An AuthenticatedSession ready to use.
    :rtype: AuthenticatedSession
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
    :type session: AuthenticatedSession
    :param action: A callable that takes ``session`` and ``*args`` and returns a result. Typically a domain
        action function (e.g., ``list_associations``, ``list_leagues``).
    :type action: Any
    :returns: The result of ``action(session, *args)`` on success.
    :rtype: Any
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
    :type ctx: Context
    :param season_id: Season ID containing the team.
    :type season_id: str
    :param team_id: Team ID to update.
    :type team_id: str
    :param title: New team name/title.
    :type title: str | None
    :param division_id: New division ID.
    :type division_id: str | None
    :param external_id: New external identifier.
    :type external_id: str | None
    :param logo_path: Path to a new logo image file.
    :type logo_path: str | None
    :param remove_logo: Remove the team's logo.
    :type remove_logo: bool
    :param output_format: Output format for rendering.
    :type output_format: str
    :param output_path: Optional output file path.
    :type output_path: str | None
    :raises Exit: If no fields are provided for update.
    :returns: None
    :rtype: None
    """
    from gamesheet_sdk.teams import Team, update_team as _update_team_action

    # Validate that at least one field is provided for update
    if all(v is None or v is False for v in (title, division_id, external_id, logo_path, remove_logo)):
        click.secho(
            f"Error: {errors.ERROR_MSG_CLI_AT_LEAST_ONE_FIELD_UPDATE}. Use --title, --division-id, "
            "--external-id, --logo-path, or --remove-logo.",
            fg="red",
            err=True,
        )
        raise Exit(1)
    config: Config = ctx.obj
    session = build_authenticated_session(config)

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
    :type ctx: Context
    :param season_id: Season ID to create the team in.
    :type season_id: str
    :param title: Team name/title.
    :type title: str
    :param division_id: Division ID the team belongs to.
    :type division_id: str
    :param external_id: Optional external identifier.
    :type external_id: str | None
    :param logo_path: Optional path to a logo image file.
    :type logo_path: str | None
    :param output_format: Output format for rendering.
    :type output_format: str
    :param output_path: Optional output file path.
    :type output_path: str | None
    :returns: None
    :rtype: None
    """
    from gamesheet_sdk.teams import create_team as _create_team_action

    config: Config = ctx.obj
    session = build_authenticated_session(config)

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


def run_team_delete(ctx: Context, season_id: str, team_id: str) -> None:
    """Run team delete action with success message.

    Shared implementation for teams delete and divisions teams delete commands.
    :param ctx: The click context containing the config.
    :type ctx: Context
    :param season_id: Season ID containing the team.
    :type season_id: str
    :param team_id: Team ID to delete.
    :type team_id: str
    """
    from gamesheet_sdk.teams import delete_team as _delete_team_action

    config: Config = ctx.obj
    session = build_authenticated_session(config)
    run_action_or_exit(session, _delete_team_action, season_id, team_id)
    click.secho(f"Team {team_id} deleted successfully.", fg="green")


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
    :type action: Any
    :param session: Authenticated session.
    :type session: AuthenticatedSession
    :param resource_type: Type of resource being assigned (player/coach).
    :type resource_type: str
    :param resource_id: ID of the resource being assigned.
    :type resource_id: str
    :param target_id: ID of the target team.
    :type target_id: str
    :param output_format: Output format for rendering.
    :type output_format: str
    :param output_path: Optional output file path.
    :type output_path: str | None
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
    :type action: Any
    :param session: Authenticated session.
    :type session: AuthenticatedSession
    :param resource_type: Type of resource being unassigned (player/coach).
    :type resource_type: str
    :param resource_id: ID of the resource being unassigned.
    :type resource_id: str
    :param target_id: ID of the target team.
    :type target_id: str
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


def run_roster_update_with_output(
    action: Any,
    session: AuthenticatedSession,
    resource_type: str,
    output_format: str,
    output_path: str | None,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Run roster update action with error handling and output rendering.

    :param action: The update action function to call.
    :type action: Any
    :param session: Authenticated session.
    :type session: AuthenticatedSession
    :param resource_type: Type of resource being updated (player/coach).
    :type resource_type: str
    :param output_format: Output format for rendering.
    :type output_format: str
    :param output_path: Optional output file path.
    :type output_path: str | None
    :raises Exit: If the action raises an exception.
    """
    from gamesheet_sdk.cli.shared import render_get_command

    try:
        with session:
            result = action(*args, **kwargs)
    except ValueError as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    except Exception as exc:
        click.secho(f"Error updating {resource_type}: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    render_get_command(result, output_format, output_path, None)
    click.secho(
        f"{resource_type.capitalize()} {result.id} updated successfully.",
        fg="green",
    )


def run_roster_create_with_output(
    action: Any,
    session: AuthenticatedSession,
    resource_type: str,
    output_format: str,
    output_path: str | None,
    *args: Any,
    success_message: str | None = None,
    **kwargs: Any,
) -> None:
    """Run roster create action with error handling and output rendering.

    :param action: The create action function to call.
    :type action: Any
    :param session: Authenticated session.
    :type session: AuthenticatedSession
    :param resource_type: Type of resource being created (player/coach).
    :type resource_type: str
    :param output_format: Output format for rendering.
    :type output_format: str
    :param output_path: Optional output file path.
    :type output_path: str | None
    :param success_message: Optional custom success message (uses result.id formatting if contains {id}).
    :type success_message: str | None
    :raises Exit: If the action raises an exception.
    """
    from gamesheet_sdk.cli.shared import render_get_command

    try:
        with session:
            result = action(*args, **kwargs)
    except Exception as exc:
        click.secho(f"Error creating {resource_type}: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    render_get_command(result, output_format, output_path, None)
    if success_message:
        message = success_message.format(id=result.id) if "{id}" in success_message else success_message
        click.secho(message, fg="green")
    else:
        click.secho(
            f"{resource_type.capitalize()} {result.id} created successfully.",
            fg="green",
        )

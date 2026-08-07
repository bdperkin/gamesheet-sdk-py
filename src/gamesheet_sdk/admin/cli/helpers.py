# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI helper functions shared across commands."""

from __future__ import annotations

from typing import Any

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

from gamesheet_sdk.common import errors
from gamesheet_sdk.common.auth.session import AuthenticatedSession
from gamesheet_sdk.common.auth.tokens import (
    load_access_token,
    load_refresh_token,
    save_tokens,
)
from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError


def build_authenticated_session(
    config: Config,
) -> AuthenticatedSession:
    """Build an AuthenticatedSession from saved tokens.

    Args:
        config (Config): The application config.

    Returns:
        AuthenticatedSession: An AuthenticatedSession ready to use.

    Raises:
        Exit: If no tokens are saved.
    """
    access = load_access_token(config)
    refresh = load_refresh_token(config)
    if access is None or refresh is None:
        click.secho(
            "No saved session found. Run `gamesheet-admin login` first.",
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

    Args:
        session (AuthenticatedSession): The authenticated session to use
            as a context manager.
        action (Any): A callable that takes ``session`` and ``*args``
            and returns a result. Typically a domain action function
            (e.g., ``list_associations``, ``list_leagues``).
        *args (Any): Positional arguments forwarded to ``action`` after
            ``session``.

    Returns:
        Any: The result of ``action(session, *args)`` on success.

    Raises:
        Exit: If ``action`` raises :exc:`AuthenticationError` or
            :exc:`GameSheetError`. Exit code is 1 in both cases.
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

    Args:
        ctx (Context): The click context containing the config.
        season_id (str): Season ID containing the team.
        team_id (str): Team ID to update.
        title (str | None): New team name/title.
        division_id (str | None): New division ID.
        external_id (str | None): New external identifier.
        logo_path (str | None): Path to a new logo image file.
        remove_logo (bool): Remove the team's logo.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.

    Raises:
        Exit: If no fields are provided for update.

    Returns:
        None: None
    """
    from gamesheet_sdk.admin.teams import Team, update_team as _update_team_action

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
    from gamesheet_sdk.admin.cli.shared import render_list_command

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

    Args:
        ctx (Context): The click context containing the config.
        season_id (str): Season ID to create the team in.
        title (str): Team name/title.
        division_id (str): Division ID the team belongs to.
        external_id (str | None): Optional external identifier.
        logo_path (str | None): Optional path to a logo image file.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.

    Returns:
        None: None
    """
    from gamesheet_sdk.admin.teams import create_team as _create_team_action

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
    from gamesheet_sdk.admin.cli.shared import render_get_command

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

    Args:
        ctx (Context): The click context containing the config.
        season_id (str): Season ID containing the team.
        team_id (str): Team ID to delete.
    """
    from gamesheet_sdk.admin.teams import delete_team as _delete_team_action

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

    Args:
        action (Any): The assign action function to call.
        session (AuthenticatedSession): Authenticated session.
        resource_type (str): Type of resource being assigned
            (player/coach).
        resource_id (str): ID of the resource being assigned.
        target_id (str): ID of the target team.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        *args (Any): Positional arguments forwarded to ``action``.
        **kwargs (Any): Keyword arguments forwarded to ``action``.

    Raises:
        Exit: If the action raises an exception.
    """
    from gamesheet_sdk.admin.cli.shared import render_get_command

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

    Args:
        action (Any): The unassign action function to call.
        session (AuthenticatedSession): Authenticated session.
        resource_type (str): Type of resource being unassigned
            (player/coach).
        resource_id (str): ID of the resource being unassigned.
        target_id (str): ID of the target team.
        *args (Any): Positional arguments forwarded to ``action``.

    Raises:
        Exit: If the action raises an exception.
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

    Args:
        action (Any): The update action function to call.
        session (AuthenticatedSession): Authenticated session.
        resource_type (str): Type of resource being updated
            (player/coach).
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        *args (Any): Positional arguments forwarded to ``action``.
        **kwargs (Any): Keyword arguments forwarded to ``action``.

    Raises:
        Exit: If the action raises an exception.
    """
    from gamesheet_sdk.admin.cli.shared import render_get_command

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

    Args:
        action (Any): The create action function to call.
        session (AuthenticatedSession): Authenticated session.
        resource_type (str): Type of resource being created
            (player/coach).
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        *args (Any): Positional arguments forwarded to ``action``.
        success_message (str | None): Optional custom success message
            (uses result.id formatting if contains {id}).
        **kwargs (Any): Keyword arguments forwarded to ``action``.

    Raises:
        Exit: If the action raises an exception.
    """
    from gamesheet_sdk.admin.cli.shared import render_get_command

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

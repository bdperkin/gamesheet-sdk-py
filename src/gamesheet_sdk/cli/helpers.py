"""CLI helper functions shared across commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from gamesheet_sdk.auth.session import AuthenticatedSession
from gamesheet_sdk.auth.tokens import load_access_token, load_refresh_token, save_tokens
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:

    from gamesheet_sdk.config import Config


def build_authenticated_session(
    _ctx: click.Context,
    config: Config,
) -> AuthenticatedSession:  # noqa: ARG001
    """Build an AuthenticatedSession from saved tokens.

    :param _ctx: The click context.
    :param config: The application config.
    :returns: An AuthenticatedSession ready to use.
    :raises click.exceptions.Exit: If no tokens are saved.
    """
    access = load_access_token(config)
    refresh = load_refresh_token(config)
    if access is None or refresh is None:

        click.secho(
            "No saved session found. Run `gamesheet-sdk-py login` first.",
            fg="red",
            err=True,
        )
        raise click.exceptions.Exit(1)
    return AuthenticatedSession(
        config,
        access_token=access,
        refresh_token=refresh,
        on_refresh=lambda tokens: save_tokens(config, **tokens),
    )


def run_action_or_exit(session: AuthenticatedSession, action: Any, *args: Any) -> Any:
    """Run an action function with error handling.

    :param session: The authenticated session.
    :param action: The action function to call.
    :param args: Arguments to pass to the action.
    :returns: The result of the action.
    :raises click.exceptions.Exit: On authentication or API errors.
    """
    try:
        with session:
            return action(session, *args)
    except AuthenticationError as exc:  # pragma: no cover - same pattern across commands
        click.secho(f"Authentication required: {exc}", fg="red", err=True)
        raise click.exceptions.Exit(1) from exc
    except GameSheetError as exc:  # pragma: no cover - same pattern across commands
        click.secho(f"GameSheet error: {exc}", fg="red", err=True)
        raise click.exceptions.Exit(1) from exc

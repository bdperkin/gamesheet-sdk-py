"""CLI helper functions shared across commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.auth.session import AuthenticatedSession
from gamesheet_sdk.auth.tokens import load_access_token, load_refresh_token, save_tokens
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:

    from gamesheet_sdk.config import Config


def build_authenticated_session(
    _ctx: click.Context,
    config: Config,
) -> AuthenticatedSession:
    """Build an AuthenticatedSession from saved tokens.

    :param _ctx: The click context.
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
    except AuthenticationError as exc:  # pragma: no cover - same pattern across commands
        click.secho(f"Authentication required: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    except GameSheetError as exc:  # pragma: no cover - same pattern across commands
        click.secho(f"GameSheet error: {exc}", fg="red", err=True)
        raise Exit(1) from exc

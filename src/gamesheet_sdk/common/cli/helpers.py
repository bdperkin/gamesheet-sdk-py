# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI helper functions shared across command modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import rich_click as click
from click import get_current_context
from click.exceptions import Exit
from click.shell_completion import get_completion_class  # type: ignore[unresolved-import]

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from collections.abc import Callable

    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession

_R = TypeVar("_R")


def run_action_or_exit(
    session: BaseAuthenticatedSession,
    action: Callable[..., _R],
    *args: object,
    **kwargs: object,
) -> _R:
    """Run an action function with error handling.

    Wraps the action call in the session's context manager and catches :exc:`AuthenticationError`
    and :exc:`GameSheetError`. On either exception, prints a user-friendly error message to
    stderr and exits with code 1. The session context manager ensures proper cleanup (e.g.,
    closing connections) regardless of success or failure.

    Args:
        session (BaseAuthenticatedSession): The authenticated session to use as a context manager.
        action (Callable[..., _R]): A callable that takes ``session`` and ``*args`` and returns
            a result. Typically a domain action function (e.g., ``list_associations``).
        *args (object): Positional arguments forwarded to ``action`` after ``session``.
        **kwargs (object): Keyword arguments forwarded to ``action``.

    Returns:
        _R: The result of ``action(session, *args, **kwargs)`` on success.

    Raises:
        Exit: If ``action`` raises :exc:`AuthenticationError` or :exc:`GameSheetError`. Exit code
            is 1 in both cases.

    """
    try:
        with session:
            return action(session, *args, **kwargs)
    except AuthenticationError as exc:
        click.secho(f"Authentication required: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    except GameSheetError as exc:
        click.secho(f"GameSheet error: {exc}", fg="red", err=True)
        raise Exit(1) from exc


def emit_shell_completion(
    shell: str,
    prog_name: str,
    complete_var: str,
) -> None:
    """Emit shell completion script for the specified shell.

    Args:
        shell (str): Target shell (bash, zsh, or fish).
        prog_name (str): The CLI program name.
        complete_var (str): Environment variable name for completion.

    Raises:
        Exit: If the specified shell is unsupported.

    """
    cls = get_completion_class(shell)
    if cls is None:  # pragma: no cover
        click.secho(f"Unsupported shell: {shell}", fg="red", err=True)
        raise Exit(1)

    ctx = get_current_context()
    if ctx.parent:
        comp = cls(
            ctx.parent.command,
            ctx_args={},
            prog_name=prog_name,
            complete_var=complete_var,
        )
        click.echo(comp.source())

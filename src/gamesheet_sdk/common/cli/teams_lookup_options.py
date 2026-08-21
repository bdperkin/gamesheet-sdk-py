# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Read-side game options that originate with the teams gateway.

``--team-id``, ``--month``, ``--event-data`` and ``--availability`` map onto real query parameters of the
teams calendar API and have no counterpart in the admin season-schedule JSON:API. They are declared here once
and accepted by both CLIs so a ``list``/``get`` command line stays portable; ``gamesheet-admin`` warns on
stderr and ignores them (see :func:`gamesheet_sdk.common.cli.game_options.warn_unsupported_options`).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import rich_click as click

from gamesheet_sdk.common.cli.game_constants import TEAMS_ONLY_SUFFIX
from gamesheet_sdk.common.cli.game_options import requiredness

F = TypeVar("F", bound=Callable[..., Any])


def team_id_option(*, required: bool, ignored: bool = False) -> Callable[[F], F]:
    """Build the standalone ``--team-id`` decorator used by ``list`` and ``get``.

    Args:
        required (bool): Whether the option is mandatory.
        ignored (bool): Whether to note in the help text that this CLI ignores it.

    Returns:
        Callable[[F], F]: The option decorator.

    """
    suffix = f" {TEAMS_ONLY_SUFFIX}" if ignored else ""

    def decorator(func: F) -> F:
        """Apply the ``--team-id`` option to ``func``.

        Args:
            func (F): The command function to decorate.

        Returns:
            F: The decorated command function.

        """
        return click.option(
            "--team-id",
            "-t",
            type=str,
            envvar="GAMESHEET_TEAM_ID",
            help=f"Team identifier.{suffix}",
            **requiredness(required=required),
        )(func)

    return decorator


def _month_option(*, ignored: bool) -> Callable[[F], F]:
    """Build the ``--month`` decorator.

    Args:
        ignored (bool): Whether to note in the help text that this CLI ignores it.

    Returns:
        Callable[[F], F]: The option decorator.

    """
    suffix = f" {TEAMS_ONLY_SUFFIX}" if ignored else ""
    return click.option(
        "--month",
        type=str,
        default="all",
        show_default=True,
        help=f"Month filter for calendar events (e.g. 'all', '2026-08').{suffix}",
    )


def _event_data_option(*, ignored: bool) -> Callable[[F], F]:
    """Build the ``--event-data`` decorator.

    Args:
        ignored (bool): Whether to note in the help text that this CLI ignores it.

    Returns:
        Callable[[F], F]: The option decorator.

    """
    suffix = f" {TEAMS_ONLY_SUFFIX}" if ignored else ""
    return click.option(
        "--event-data",
        "--include-event-data",
        "include_event_data",
        is_flag=True,
        default=False,
        help=f"Include detailed eventData in the output.{suffix}",
    )


def list_filter_options(*, team_required: bool, ignored: bool = False) -> Callable[[F], F]:
    """Build the decorator adding ``--team-id``, ``--month`` and ``--event-data`` to a ``list`` command.

    Args:
        team_required (bool): Whether ``--team-id`` is mandatory. Only ``gamesheet-teams`` needs it.
        ignored (bool): Whether this CLI ignores all three.

    Returns:
        Callable[[F], F]: The option decorator.

    """

    def decorator(func: F) -> F:
        """Apply the list filter options to ``func``.

        Args:
            func (F): The command function to decorate.

        Returns:
            F: The decorated command function.

        """
        func = _event_data_option(ignored=ignored)(func)
        func = _month_option(ignored=ignored)(func)
        return team_id_option(required=team_required, ignored=ignored)(func)

    return decorator


def availability_options(*, ignored: bool = False) -> Callable[[F], F]:
    """Build the decorator adding ``--availability`` and ``--team-id`` to a ``get`` command.

    Args:
        ignored (bool): Whether this CLI ignores both.

    Returns:
        Callable[[F], F]: The option decorator.

    """
    suffix = f" {TEAMS_ONLY_SUFFIX}" if ignored else ""

    def decorator(func: F) -> F:
        """Apply the availability options to ``func``.

        Args:
            func (F): The command function to decorate.

        Returns:
            F: The decorated command function.

        """
        func = team_id_option(required=False, ignored=ignored)(func)
        return click.option(
            "--availability",
            "--include-availability",
            "include_availability",
            is_flag=True,
            default=False,
            help=f"Include player/coach availability for the game.{suffix}",
        )(func)

    return decorator


__all__ = [
    "availability_options",
    "list_filter_options",
    "team_id_option",
]

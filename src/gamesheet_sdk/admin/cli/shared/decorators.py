# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Common CLI option decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import rich_click as click
from rich_click import Path

from gamesheet_sdk.admin.cli.constants import (
    HELP_UPDATED_EXTERNAL_ID,
    HELP_UPDATED_FIRST_NAME,
    HELP_UPDATED_LAST_NAME,
)
from gamesheet_sdk.common.cli.decorators import (
    columns_option,
    common_output_options,
)

F = TypeVar("F", bound=Callable[..., object])

__all__ = [
    "columns_option",
    "common_output_options",
    "player_update_options",
    "team_create_options",
    "team_update_options",
]


def team_update_options(func: F) -> F:
    """Add common team update options.

    Args:
        func (F): The Click command function to decorate

    Returns:
        F: The decorated function with team update options

    """
    func = click.option(
        "--title",
        type=str,
        default=None,
        help="New team name/title.",
    )(func)
    func = click.option(
        "--division-id",
        type=str,
        default=None,
        help="New division ID.",
    )(func)
    func = click.option(
        "--external-id",
        type=str,
        default=None,
        help="New external identifier.",
    )(func)
    func = click.option(
        "--logo",
        "logo_path",
        type=Path(exists=True, dir_okay=False),
        help="Path to a new logo image file.",
    )(func)
    return click.option(
        "--remove-logo",
        is_flag=True,
        default=False,
        help="Remove the team's logo.",
    )(func)


def team_create_options(func: F) -> F:
    """Add common team create options.

    Args:
        func (F): The Click command function to decorate

    Returns:
        F: The decorated function with team create options

    """
    func = click.option(
        "--external-id",
        type=str,
        default=None,
        help="Optional external identifier for the team.",
    )(func)
    return click.option(
        "--logo",
        "logo_path",
        type=Path(exists=True, dir_okay=False),
        help="Optional path to a local logo image file.",
    )(func)


def player_update_options(func: F) -> F:
    """Add common player update options.

    Args:
        func (F): The Click command function to decorate

    Returns:
        F: The decorated function with player update options

    """
    options = [
        click.option(
            "--first-name",
            type=str,
            help=HELP_UPDATED_FIRST_NAME,
        ),
        click.option(
            "--last-name",
            type=str,
            help=HELP_UPDATED_LAST_NAME,
        ),
        click.option(
            "--external-id",
            type=str,
            help=HELP_UPDATED_EXTERNAL_ID,
        ),
        click.option(
            "--biography",
            type=str,
            help="Updated biography text.",
        ),
        click.option(
            "--height",
            type=str,
            help="Updated height (e.g., 6'2\").",
        ),
        click.option(
            "--weight",
            type=str,
            help="Updated weight (e.g., 185).",
        ),
        click.option(
            "--shot-hand",
            type=click.Choice(["left", "right"], case_sensitive=False),
            help="Updated shooting hand.",
        ),
        click.option(
            "--birthdate",
            type=str,
            help="Updated birthdate (ISO format: YYYY-MM-DD).",
        ),
        click.option(
            "--hometown",
            type=str,
            help="Updated hometown.",
        ),
        click.option(
            "--country",
            type=str,
            help="Updated country code (e.g., US, CA).",
        ),
        click.option(
            "--province",
            type=str,
            help="Updated province/state.",
        ),
        click.option(
            "--drafted-by",
            type=str,
            help="Updated drafted by team name.",
        ),
        click.option(
            "--committed-to",
            type=str,
            help="Updated committed to institution.",
        ),
        click.option(
            "--photo",
            "photo_path",
            type=click.Path(exists=True, dir_okay=False),
            help="Path to a new photo image file.",
        ),
        click.option(
            "--remove-photo",
            is_flag=True,
            default=False,
            help="Remove the player's photo.",
        ),
    ]
    for opt in reversed(options):
        func = opt(func)

    return func

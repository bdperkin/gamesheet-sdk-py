# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Common CLI option decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import rich_click as click
from rich_click import Path

from gamesheet_sdk.common.cli.decorators import (
    common_output_options,
    get_fields_option,
    list_columns_option,
)

F = TypeVar("F", bound=Callable[..., object])

__all__ = [
    "common_output_options",
    "get_fields_option",
    "list_columns_option",
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

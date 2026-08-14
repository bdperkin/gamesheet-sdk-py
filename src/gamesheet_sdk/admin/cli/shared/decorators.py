# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Common CLI option decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import rich_click as click
from rich_click import Choice, Path

from gamesheet_sdk.common.output import ALL_FORMATS, DEFAULT_FORMAT

F = TypeVar("F", bound=Callable[..., object])


def common_output_options(func: F) -> F:
    """Add standard --format and --output options to command.

    Args:
        func (F): The Click command function to decorate

    Returns:
        F: The decorated function with --format and --output options

    """
    func = click.option(
        "--format",
        "-F",
        "output_format",
        type=Choice(list(ALL_FORMATS), case_sensitive=False),
        default=DEFAULT_FORMAT,
        show_default=True,
        help=(
            "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
            "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
            "rst, mediawiki, html, latex, latex_raw, latex_booktabs, latex_longtable."
        ),
    )(func)
    return click.option(
        "--output",
        "-o",
        "output_path",
        type=Path(dir_okay=False, writable=True),
        default=None,
        help="Write to this file instead of stdout.",
    )(func)


def list_columns_option(func: F) -> F:
    """Add --columns option for list commands.

    Args:
        func (F): The Click command function to decorate

    Returns:
        F: The decorated function with --columns option

    """
    return click.option(
        "--columns",
        "-c",
        "columns_spec",
        default=None,
        help="Comma-separated list of column names to include (default: all columns the API returns).",
    )(func)


def get_fields_option(func: F) -> F:
    """Add --fields option for get commands.

    Args:
        func (F): The Click command function to decorate

    Returns:
        F: The decorated function with --fields option

    """
    return click.option(
        "--fields",
        "-f",
        "fields_spec",
        default=None,
        help="Comma-separated list of field names to include (default: all fields the API returns).",
    )(func)


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

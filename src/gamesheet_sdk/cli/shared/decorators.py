"""Common CLI option decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import rich_click as click
from rich_click import Choice, Path

from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT

F = TypeVar("F", bound=Callable[..., object])


def common_output_options(func: F) -> F:
    """Add standard --format and --output options to command.

    Args:
        func: The Click command function to decorate

    Returns:
        The decorated function with --format and --output options
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
    func = click.option(
        "--output",
        "-o",
        "output_path",
        type=Path(dir_okay=False, writable=True),
        default=None,
        help="Write to this file instead of stdout.",
    )(func)
    return func


def list_columns_option(func: F) -> F:
    """Add --columns option for list commands.

    Args:
        func: The Click command function to decorate

    Returns:
        The decorated function with --columns option
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
        func: The Click command function to decorate

    Returns:
        The decorated function with --fields option
    """
    return click.option(
        "--fields",
        "-f",
        "fields_spec",
        default=None,
        help="Comma-separated list of field names to include (default: all fields the API returns).",
    )(func)

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Common CLI option decorators for all GameSheet CLIs."""

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


def fields_option(*, short: bool) -> Callable[[F], F]:
    """Build the --fields decorator, optionally without its ``-f`` short flag.

    Delete commands pass ``short=False`` so that ``-f`` unambiguously means ``--force`` there, as it does for
    every other destructive command in both CLIs.

    Args:
        short (bool): Whether to also bind ``-f``.

    Returns:
        Callable[[F], F]: The option decorator.

    """
    names = ["--fields", "-f", "fields_spec"] if short else ["--fields", "fields_spec"]

    def decorator(func: F) -> F:
        """Apply the --fields option to ``func``.

        Args:
            func (F): The Click command function to decorate.

        Returns:
            F: The decorated function.

        """
        return click.option(
            *names,
            default=None,
            help="Comma-separated list of field names to include (default: all fields the API returns).",
        )(func)

    return decorator


def get_fields_option(func: F) -> F:
    """Add --fields option for get commands.

    Args:
        func (F): The Click command function to decorate

    Returns:
        F: The decorated function with --fields option

    """
    return fields_option(short=True)(func)

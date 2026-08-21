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


def columns_option(func: F) -> F:
    """Add the --columns option that restricts output to a subset of keys.

    One option covers both shapes of output: on a ``list`` it selects table columns, and on a ``get`` /
    ``create`` / ``update`` it selects fields of the single rendered object. Both are "show me only these
    keys", so there is one name for it, and ``-f`` is left to mean ``--force`` everywhere.

    Args:
        func (F): The Click command function to decorate.

    Returns:
        F: The decorated function with the --columns option.

    """
    return click.option(
        "--columns",
        "-c",
        "columns_spec",
        default=None,
        help="Comma-separated list of column names to include (default: all columns the API returns).",
    )(func)

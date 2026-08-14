# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Lookups command for the GameSheet teams dashboard.

Fetches public enumeration data (sports, positions, game types, etc.) from the teams API.  No authentication
is required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Choice, Context, Path

from gamesheet_sdk.common.cli.core import ResourceGroup
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.output import (
    ALL_FORMATS,
    DEFAULT_FORMAT,
    render,
    write_output,
)
from gamesheet_sdk.teams.lookups import LookupValue, list_lookups

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


@click.group(
    "lookups",
    cls=ResourceGroup,
    default="list",
    aliases={"get": ("show", "view"), "list": ("ls",)},
    context_settings={"help_option_names": ["-h", "--help"]},
)
def lookups_group() -> None:
    """View public lookup/enumeration data from the teams API."""


def _render_category(
    lookups: dict[str, list[LookupValue]],
    category: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Render values for a single category."""
    if category not in lookups:
        available = ", ".join(sorted(lookups))
        click.secho(
            f"Unknown category '{category}'. Available: {available}",
            fg="red",
            err=True,
        )
        raise Exit(1)

    rows = [v.model_dump(mode="json") for v in lookups[category]]
    rendered = render(rows, fmt=output_format)
    write_output(rendered, output_path, fmt=output_format)


def _render_summary(
    lookups: dict[str, list[LookupValue]],
    output_format: str,
    output_path: str | None,
) -> None:
    """Render a summary of all categories."""
    if output_format in ("json", "yaml"):
        full = {cat: [v.model_dump(mode="json") for v in vals] for cat, vals in lookups.items()}
        rendered = render([full], fmt=output_format)
    else:
        rows = [{"category": cat, "count": len(vals)} for cat, vals in sorted(lookups.items())]
        rendered = render(rows, fmt=output_format)

    write_output(rendered, output_path, fmt=output_format)


@lookups_group.command("get")
@click.option(
    "--category",
    "-c",
    required=True,
    help="Category to retrieve values for.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
def get_command(
    ctx: Context,
    category: str,
    output_format: str,
    output_path: str | None,
) -> None:
    r"""Get values for a specific lookup category.

    Fetches all lookup data and renders the values for the given category.\f

    Args:
        ctx (Context): Click context carrying the :class:`~gamesheet_sdk.common.config.Config` instance.
        category (str): Category name to retrieve.
        output_format (str): Output format (json, yaml, csv, tsv, or tabulate format).
        output_path (str | None): Optional file path to write output to.

    """
    config: Config = ctx.obj
    try:
        lookups = list_lookups(timeout=config.timeout)
    except GameSheetError as exc:
        click.secho(str(exc), fg="red", err=True)
        raise Exit(1) from exc

    _render_category(lookups, category, output_format, output_path)


@lookups_group.command("list")
@click.option(
    "--category",
    "-c",
    default=None,
    help="Show values for a specific category only.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
def list_command(
    ctx: Context,
    category: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    r"""List lookup categories or values within a category.

    Without ``--category``, shows a summary of all available categories and their value counts.  With
    ``--category``, shows every value in that category.\f

    Args:
        ctx (Context): Click context carrying the :class:`~gamesheet_sdk.common.config.Config` instance.
        category (str | None): Optional category name to filter to.
        output_format (str): Output format (json, yaml, csv, tsv, or tabulate format).
        output_path (str | None): Optional file path to write output to.

    """
    config: Config = ctx.obj
    try:
        lookups = list_lookups(timeout=config.timeout)
    except GameSheetError as exc:
        click.secho(str(exc), fg="red", err=True)
        raise Exit(1) from exc

    if category is not None:
        _render_category(lookups, category, output_format, output_path)
    else:
        _render_summary(lookups, output_format, output_path)

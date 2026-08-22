# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Bracket games CLI commands."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.admin.cli.shared import columns_option, common_output_options
from gamesheet_sdk.common.cli.core import ResourceGroup


@click.group(
    "brackets",
    cls=ResourceGroup,
    default="list",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def brackets_group() -> None:
    """Manage bracket games.

    Invoking ``brackets`` with no sub-command runs ``list`` by default.
    """


@brackets_group.command("list", aliases=["ls"])
@columns_option
@common_output_options
def brackets_list_command(
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all bracket games in the specified season.

    NOT YET IMPLEMENTED - Bracket games support is planned for a future release.\f

    Args:
        output_format (str): Output format (ignored - command not implemented).
        output_path (str | None): Output file path (ignored - command not implemented).
        columns_spec (str | None): Columns specification (ignored - command not implemented).

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    # Click binds these by their declared option names, so they cannot be underscore-prefixed.
    _ = (output_format, output_path, columns_spec)
    click.secho(
        "Error: games brackets list is not yet implemented. "
        "Bracket games support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)

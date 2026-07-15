# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Bracket games CLI commands."""

from __future__ import annotations

from click.exceptions import Exit
import rich_click as click

from gamesheet_sdk.admin.cli.shared import common_output_options, list_columns_option
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
@list_columns_option
@common_output_options
def brackets_list_command(
    # pylint: disable-next=unused-argument
    output_format: str,  # noqa: U100
    # pylint: disable-next=unused-argument
    output_path: str | None,  # noqa: U100
    # pylint: disable-next=unused-argument
    columns_spec: str | None,  # noqa: U100
) -> None:
    """List all bracket games in the specified season.

    NOT YET IMPLEMENTED - Bracket games support is planned for a future release.

    :param output_format: Output format (ignored - command not implemented).
    :type output_format: str
    :param output_path: Output file path (ignored - command not implemented).
    :type output_path: str | None
    :param columns_spec: Columns specification (ignored - command not implemented).
    :type columns_spec: str | None
    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    click.secho(
        "Error: games brackets list is not yet implemented. "
        "Bracket games support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Roster CLI commands for GameSheet teams."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.common.cli.core import ResourceGroup


@click.group(
    "roster",
    cls=ResourceGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def roster_group() -> None:
    """Manage team rosters, coaches, and players."""


@roster_group.command("import")
def roster_import_command() -> None:
    r"""Import roster data.

    Import team roster members and player information.\f

    NOT YET IMPLEMENTED - Roster import support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: roster import is not yet implemented. Roster import support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@roster_group.command("coaches")
def roster_coaches_command() -> None:
    r"""Manage team coaches.

    View and manage team coaching staff.\f

    NOT YET IMPLEMENTED - Coaches support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: roster coaches is not yet implemented. Coaches support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@roster_group.command("players")
def roster_players_command() -> None:
    r"""Manage team players.

    View and manage team player roster.\f

    NOT YET IMPLEMENTED - Players support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: roster players is not yet implemented. Players support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)

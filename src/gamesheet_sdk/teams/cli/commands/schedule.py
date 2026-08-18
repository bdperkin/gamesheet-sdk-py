# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule CLI commands for GameSheet teams."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.common.cli.core import ResourceGroup


@click.group(
    "schedule",
    cls=ResourceGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def schedule_group() -> None:
    """Manage team schedules, calendar events, practices, and games."""


@schedule_group.command("export")
def schedule_export_command() -> None:
    r"""Export and download scoresheets.

    Download team scoresheets and game data.\f

    NOT YET IMPLEMENTED - Scoresheet export support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: schedule export is not yet implemented. "
        "Scoresheet export support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@schedule_group.command("subscribe")
def schedule_subscribe_command() -> None:
    r"""Subscribe to team calendar.

    Generate calendar subscription feed URL.\f

    NOT YET IMPLEMENTED - Calendar subscription support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: schedule subscribe is not yet implemented. "
        "Calendar subscription support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@schedule_group.command("practices")
def schedule_practices_command() -> None:
    r"""Manage practice schedules.

    View and manage team practice sessions.\f

    NOT YET IMPLEMENTED - Practices support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: schedule practices is not yet implemented. "
        "Practices support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@schedule_group.command("events")
def schedule_events_command() -> None:
    r"""Manage calendar events.

    View and manage team calendar events.\f

    NOT YET IMPLEMENTED - Calendar events support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: schedule events is not yet implemented. "
        "Calendar events support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@schedule_group.command("games")
def schedule_games_command() -> None:
    r"""Manage scheduled games.

    View and manage scheduled team games.\f

    NOT YET IMPLEMENTED - Scheduled games support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: schedule games is not yet implemented. "
        "Scheduled games support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)

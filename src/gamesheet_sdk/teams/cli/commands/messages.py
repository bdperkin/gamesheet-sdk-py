# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Messages CLI commands for GameSheet teams."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit


@click.command("messages")
def messages_command() -> None:
    r"""Manage team messages and chat conversations.

    NOT YET IMPLEMENTED - Messages and chat support is planned for a future release.\f

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: messages is not yet implemented. Messages and chat support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)

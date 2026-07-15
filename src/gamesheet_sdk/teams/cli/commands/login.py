# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Login command for the GameSheet teams dashboard (stub).

The teams authentication flow has not been reverse-engineered yet. This command is a placeholder so the CLI
surface is consistent between ``gamesheet-admin`` and ``gamesheet-teams``.
"""

from __future__ import annotations

from click.exceptions import Exit
import rich_click as click


@click.command("login")
@click.option(
    "--email",
    "-e",
    envvar="GAMESHEET_USERNAME",
    help="Email address (or set GAMESHEET_USERNAME).",
)
@click.option(
    "--password",
    "-p",
    envvar="GAMESHEET_PASSWORD",
    help="Password (or set GAMESHEET_PASSWORD). Prompted if omitted.",
    hide_input=True,
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    default=30000,
    help="Page-load timeout in milliseconds.",
)
def login_command(
    # pylint: disable-next=unused-argument
    email: str | None,  # noqa: U100
    # pylint: disable-next=unused-argument
    password: str | None,  # noqa: U100
    # pylint: disable-next=unused-argument
    timeout: int,  # noqa: U100
) -> None:
    """Authenticate with the GameSheet teams dashboard and save session tokens.

    .. warning::

        This command is not yet implemented. The teams authentication flow
        is pending discovery and will be added in a future release.

    :param email: Email address for login, or ``None`` to use the environment variable.
    :type email: str | None
    :param password: Password for login, or ``None`` to prompt interactively.
    :type password: str | None
    :param timeout: Page-load timeout in milliseconds.
    :type timeout: int
    """
    click.secho("Teams login is not yet implemented.", fg="yellow", err=True)
    raise Exit(1)

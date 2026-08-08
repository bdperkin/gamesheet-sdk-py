# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Login command for the GameSheet teams dashboard.

Authenticates via HTTP-only Firebase REST + teams API token exchange (no headless browser required) and
persists session tokens to disk.
"""

from __future__ import annotations

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.teams.login import TeamsLoginFlow


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
    type=float,
    default=15.0,
    help="HTTP request timeout in seconds.",
)
@click.pass_context
def login_command(
    ctx: Context,
    email: str | None,
    password: str | None,
    timeout: float,
) -> None:
    """Authenticate with the GameSheet teams dashboard and save session tokens.

    Sends credentials to Firebase Auth, exchanges the ID token for application tokens via the teams API
    gateway, and saves the result to disk so subsequent commands can authenticate automatically.\f

    Args:
        ctx (Context): Click context carrying the
            :class:`~gamesheet_sdk.common.config.Config` instance.
        email (str | None): Email address for login, or ``None`` to use
            the environment variable.
        password (str | None): Password for login, or ``None`` to prompt
            interactively.
        timeout (float): HTTP request timeout in seconds.
    """
    config: Config = ctx.obj
    try:
        TeamsLoginFlow(config).authenticate(
            email=email,
            password=password,
            timeout=timeout,
        )
    except Exception as exc:
        click.secho(f"Login failed: {exc}", fg="red", err=True)
        raise Exit(1) from exc

    click.secho("Login successful! Tokens saved.", fg="green")

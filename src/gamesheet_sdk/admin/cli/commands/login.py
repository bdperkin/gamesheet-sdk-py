# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Login command for the GameSheet admin dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Context

from gamesheet_sdk.common.auth.login import login as _login_action
from gamesheet_sdk.common.browser import BrowserSession

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


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
@click.pass_context
def login_command(
    ctx: Context,
    email: str | None,
    password: str | None,
    timeout: int,
) -> None:
    r"""Authenticate with the GameSheet admin dashboard and save session tokens.

    Opens a headless browser, navigates to the admin login page, submits credentials, and extracts
    authentication tokens. Tokens are saved to disk so subsequent commands can authenticate without launching
    a browser.\f

    Args:
        ctx (Context): Click context carrying the :class:`~gamesheet_sdk.common.config.Config` instance.
        email (str | None): Email address for login, or ``None`` to use the environment variable.
        password (str | None): Password for login, or ``None`` to prompt interactively.
        timeout (int): Page-load timeout in milliseconds.

    """
    config: Config = ctx.obj
    try:
        with BrowserSession(config) as session:
            _login_action(session, email=email, password=password, timeout=timeout)
    except Exception as exc:
        click.secho(f"Login failed: {exc}", fg="red", err=True)
        raise Exit(1) from exc

    click.secho("Login successful! Tokens saved.", fg="green")

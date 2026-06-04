"""Login command."""

from __future__ import annotations

import click

from gamesheet_sdk.auth.login import login as _login_action
from gamesheet_sdk.browser import BrowserSession
from gamesheet_sdk.config import Config


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
def login_command(  # pragma: no cover - requires browser automation
    ctx: click.Context,
    email: str | None,
    password: str | None,
    timeout: int,
) -> None:
    """Authenticate and save session tokens.

    Opens a headless Chromium browser, navigates to the GameSheet login page, submits your credentials, waits
    for the post-login redirect, and extracts ``accessToken`` and ``refreshToken`` from the browser's

    localStorage. Both tokens are persisted to :attr:`Config.browser_state_path` so subsequent commands pick
    them up without re-authenticating.
    """
    config: Config = ctx.obj
    try:  # pragma: no cover
        with BrowserSession(config) as session:
            _login_action(session, email=email, password=password, timeout=timeout)
    except Exception as exc:  # pragma: no cover - browser errors
        click.secho(f"Login failed: {exc}", fg="red", err=True)
        raise click.exceptions.Exit(1) from exc
    click.secho("Login successful! Tokens saved.", fg="green")

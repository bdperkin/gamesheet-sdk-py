# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Login command for GameSheet authentication.

This module provides the CLI interface for authenticating with the GameSheet platform via browser-based
login. The login flow launches a headless Chromium browser, navigates to the GameSheet login page, submits
credentials, and extracts authentication tokens (accessToken and refreshToken) from the browser's
localStorage after successful authentication.
Tokens are persisted to disk so subsequent CLI commands can reuse the session without re-authenticating.
The saved browser state includes cookies and any SPA-cached data, enabling fully authenticated HTTP
requests without launching a browser.
Examples:
    Authenticate interactively (email provided, password prompted)::
        $ gamesheet-sdk-py login --email user@example.com
    Authenticate with both email and password from command line::
        $ gamesheet-sdk-py login --email user@example.com --password secret
    Authenticate using environment variables::
        $ export GAMESHEET_USERNAME=user@example.com
        $ export GAMESHEET_PASSWORD=secret
        $ gamesheet-sdk-py login
    Authenticate with custom timeout for slow connections::
        $ gamesheet-sdk-py login --email user@example.com --timeout 60000
    Debug login issues with visible browser::
        $ gamesheet-sdk-py login --email user@example.com --no-headless -vv
"""

from __future__ import annotations

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

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
def login_command(
    ctx: Context,
    email: str | None,
    password: str | None,
    timeout: int,
) -> None:
    """Authenticate with GameSheet and save session tokens.

    Opens a headless browser, navigates to the GameSheet login page, submits your
    credentials, and extracts authentication tokens. Tokens are saved to disk so
    subsequent commands can authenticate without launching a browser.
    Credentials can be provided via --email and --password options, environment
    variables (GAMESHEET_USERNAME, GAMESHEET_PASSWORD), or interactively (password
    is prompted if omitted). If already authenticated from a previous login, the
    command returns immediately.
    .. rubric:: Examples

        Authenticate with email, password prompted:
    .. code-block:: bash

        $ gamesheet-sdk-py login --email user@example.com
        Password: [hidden input]
        Login successful! Tokens saved.

        Authenticate with both credentials from command line:
    .. code-block:: bash

        $ gamesheet-sdk-py login --email user@example.com --password secret
        Login successful! Tokens saved.

        Authenticate using environment variables:
    .. code-block:: bash

        $ export GAMESHEET_USERNAME=user@example.com

    .. code-block:: bash

        $ export GAMESHEET_PASSWORD=secret

    .. code-block:: bash

        $ gamesheet-sdk-py login
        Login successful! Tokens saved.

        Authenticate with extended timeout:
    .. code-block:: bash

        $ gamesheet-sdk-py login --email user@example.com --timeout 60000

        Debug login flow with visible browser and verbose logging:
    .. code-block:: bash

        $ gamesheet-sdk-py login --email user@example.com --no-headless -vv

        Force fresh login by clearing saved state:
    .. code-block:: bash

        $ rm ~/.local/share/gamesheet-sdk-py/browser_state

    .. code-block:: bash

        $ gamesheet-sdk-py login --email user@example.com

    :param ctx: Click context object containing config
    :type ctx: Context
    :param email: Optional email address for authentication
    :type email: str | None
    :param password: Optional password for authentication
    :type password: str | None
    :param timeout: Browser operation timeout in milliseconds
    :type timeout: int
    :raises Exit: If login fails
    """
    config: Config = ctx.obj
    try:
        with BrowserSession(config) as session:
            _login_action(session, email=email, password=password, timeout=timeout)
    except Exception as exc:
        click.secho(f"Login failed: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    click.secho("Login successful! Tokens saved.", fg="green")

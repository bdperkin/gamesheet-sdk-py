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
    """Authenticate with GameSheet and save session tokens.

    Opens a headless Chromium browser, navigates to the GameSheet login page, submits your credentials, waits
    for the Firebase authentication and token exchange to complete, and extracts ``accessToken`` and
    ``refreshToken`` from the browser's localStorage.  Both tokens are persisted
    to :attr:`~gamesheet_sdk.config.Config.browser_state_path`
    (``~/.local/share/gamesheet-sdk-py/browser_state``) so subsequent commands can authenticate via HTTP
    without launching a browser.

    Credentials can be provided via command-line options (``--email``, ``--password``), environment variables
    (``GAMESHEET_USERNAME``, ``GAMESHEET_PASSWORD``), or interactively (password is prompted if omitted from
    all sources). The authentication flow waits for both Firebase Auth and the GameSheet token exchange to
    return HTTP 200; failure at either stage surfaces the backend error message (e.g., ``EMAIL_NOT_FOUND``,
    ``INVALID_LOGIN_CREDENTIALS``, ``TOO_MANY_ATTEMPTS_TRY_LATER``).

    After successful authentication, the command navigates to ``/associations`` to allow the GameSheet SPA to
    finish initialization and populate permissions/association data in the browser state. This ensures the
    saved state represents a fully authenticated session, not just bare auth cookies.

    If the saved browser state already authenticates the user (e.g., from a previous login that hasn't
    expired), the login form is skipped and the command returns immediately. To force a fresh login (e.g., to
    switch accounts), delete the browser state file first.

    :param ctx: Click context object containing the application :class:`~gamesheet_sdk.config.Config` in
        ``ctx.obj``.
    :param email: Email address for GameSheet account. Falls back to ``GAMESHEET_USERNAME`` environment
        variable, then to :attr:`~gamesheet_sdk.config.Config.username`. If not available from any source, the
        command fails.
    :param password: Password for GameSheet account. Falls back to ``GAMESHEET_PASSWORD`` environment
        variable, then to :attr:`~gamesheet_sdk.config.Config.password`. If not available from any source, the
        user is prompted interactively (input hidden).
    :param timeout: Maximum time in milliseconds to wait for the authentication backend round-trip (Firebase
        Auth + token exchange). Defaults to 30000 (30 seconds). Increase this on slow connections.
    :returns: None. Prints success message to stdout on completion or exits with code 1 on failure.
    :raises click.exceptions.Exit: If authentication fails (missing credentials, Firebase rejection, token
        exchange error, or backend timeout), the command prints an error message to stderr and exits with code
        1.

    Examples:
        Authenticate with email, password prompted::

            $ gamesheet-sdk-py login --email user@example.com
            Password: [hidden input]
            Login successful! Tokens saved.

        Authenticate with both credentials from command line::

            $ gamesheet-sdk-py login --email user@example.com --password secret
            Login successful! Tokens saved.

        Authenticate using environment variables::

            $ export GAMESHEET_USERNAME=user@example.com
            $ export GAMESHEET_PASSWORD=secret
            $ gamesheet-sdk-py login
            Login successful! Tokens saved.

        Authenticate with extended timeout::

            $ gamesheet-sdk-py login --email user@example.com --timeout 60000

        Debug login flow with visible browser and verbose logging::

            $ gamesheet-sdk-py login --email user@example.com --no-headless -vv

        Force fresh login by clearing saved state::

            $ rm ~/.local/share/gamesheet-sdk-py/browser_state
            $ gamesheet-sdk-py login --email user@example.com
    """
    config: Config = ctx.obj
    try:  # pragma: no cover
        with BrowserSession(config) as session:
            _login_action(session, email=email, password=password, timeout=timeout)
    except Exception as exc:  # pragma: no cover - browser errors
        click.secho(f"Login failed: {exc}", fg="red", err=True)
        raise click.exceptions.Exit(1) from exc
    click.secho("Login successful! Tokens saved.", fg="green")

"""Command-line entry point for gamesheet_sdk.

Built on click. The pyproject.toml entry point is
``gamesheet_sdk.cli:main``; ``main`` is a thin int-returning wrapper
around the click group ``cli`` so the original
``main(argv: list[str] | None = None) -> int`` contract is preserved
for callers that imported it directly.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import click

from . import __version__
from .auth import login as _login_action
from .browser import BrowserSession
from .config import Config
from .exceptions import AuthenticationError


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(__version__, prog_name="gamesheet-sdk-py")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase logging verbosity. -v sets INFO; -vv sets DEBUG.",
)
@click.option(
    "--base-url",
    metavar="URL",
    help="Override Config.base_url for this invocation.",
)
@click.option(
    "--no-headless",
    is_flag=True,
    help="Run browser-driven flows with a visible window (for debugging).",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: int,
    base_url: str | None,
    no_headless: bool,
) -> None:
    """Unofficial CLI for the GameSheet Inc. platform.

    Each subcommand resolves its configuration in this order: CLI args >
    GAMESHEET_* environment variables > built-in defaults.
    """
    _configure_logging(verbose)
    overrides: dict[str, Any] = {}
    if base_url is not None:
        overrides["base_url"] = base_url
    if no_headless:
        overrides["browser_headless"] = False
    ctx.obj = Config(**overrides)
    # `invoke_without_command=True` lets us reach here with no subcommand;
    # in that case we print help and exit 0 (the canonical user-friendly
    # default) rather than letting click report a "Missing command" error.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _configure_logging(verbose: int) -> None:
    """Configure root logging based on the verbosity count (0, 1, 2+)."""
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,  # let repeat calls re-set the level
    )


@cli.command("login")
@click.option(
    "--email",
    "-e",
    envvar="GAMESHEET_USERNAME",
    prompt="Email",
    help="GameSheet account email. Falls back to GAMESHEET_USERNAME, then prompts.",
)
@click.option(
    "--password",
    "-p",
    envvar="GAMESHEET_PASSWORD",
    prompt=True,
    hide_input=True,
    help="GameSheet account password. Falls back to GAMESHEET_PASSWORD, then prompts.",
)
@click.option(
    "--timeout",
    type=float,
    default=15.0,
    show_default=True,
    help="Seconds to wait for the post-submit redirect off the sign-in page.",
)
@click.pass_context
def login_command(
    ctx: click.Context,
    email: str,
    password: str,
    timeout: float,
) -> None:
    """Authenticate against the GameSheet dashboard and persist the session.

    On success the auth cookie and browser storage state are written to
    ``Config.browser_state_path`` so subsequent commands pick them up
    without re-authenticating.
    """
    config: Config = ctx.obj
    try:
        with BrowserSession(config) as session:
            _login_action(session, email=email, password=password, timeout=timeout)
    except AuthenticationError as exc:
        click.secho(f"Login failed: {exc}", fg="red", err=True)
        ctx.exit(1)  # raises; nothing after this point in the except runs
    click.secho("Login succeeded.", fg="green")


def main(  # pylint: disable=too-many-return-statements
    argv: list[str] | None = None,
) -> int:
    """Entry-point wrapper. Returns an int exit code.

    Calls into the click ``cli`` group with ``standalone_mode=False`` so
    click's control-flow exceptions are converted to integer returns
    rather than ``sys.exit()`` calls, preserving the original
    ``main(argv) -> int`` contract.
    """
    try:
        cli.main(
            args=argv,
            prog_name="gamesheet-sdk-py",
            standalone_mode=False,
        )
    except click.exceptions.Exit as exc:
        return int(exc.exit_code)
    except click.exceptions.UsageError as exc:
        exc.show()
        return 2
    except click.exceptions.Abort:
        click.echo("Aborted.", err=True)
        return 1
    except SystemExit as exc:
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command-line entry point for gamesheet_sdk.

Built on click. The pyproject.toml entry point is
``gamesheet_sdk.cli:main``; ``main`` is a thin int-returning wrapper
around the click group ``cli`` so the original
``main(argv: list[str] | None = None) -> int`` contract is preserved
for callers that imported it directly.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

import click
import colorlog

from . import __version__
from .associations import list_associations as _list_associations_action
from .auth import (
    AuthenticatedSession,
    load_access_token,
    load_refresh_token,
)
from .auth import login as _login_action
from .auth import save_tokens
from .browser import BrowserSession
from .config import Config
from .exceptions import AuthenticationError, GameSheetError


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
    """Configure root logging based on the verbosity count (0, 1, 2+).

    Uses :class:`colorlog.ColoredFormatter` to add ANSI color codes to
    each log level when stderr is a TTY and the user has not set the
    ``NO_COLOR`` environment variable (https://no-color.org/). Falls
    back to a plain :class:`logging.Formatter` for non-interactive
    output (e.g. piped to a file or running in CI), so escape codes
    never leak into log files.
    """
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    handler = logging.StreamHandler()  # defaults to sys.stderr
    if _should_color(handler):
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)-8s%(reset)s "
                "%(message_log_color)s%(message)s",
                datefmt=None,
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
                secondary_log_colors={"message": {"ERROR": "red", "CRITICAL": "red"}},
                style="%",
            )
        )
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=level, handlers=[handler], force=True)


def _should_color(handler: logging.StreamHandler[Any]) -> bool:
    """Return True iff the handler's stream is a TTY and color is permitted."""
    if os.environ.get("NO_COLOR"):
        return False
    stream = getattr(handler, "stream", None)
    return bool(stream is not None and getattr(stream, "isatty", lambda: False)())


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


@cli.command("list-associations")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format: tab-separated table or JSON array.",
)
@click.pass_context
def list_associations_command(
    ctx: click.Context,
    output_format: str,
) -> None:
    """List the associations the signed-in user can see.

    Requires a saved session from `gamesheet-sdk-py login` -- the bearer
    token is read out of the browser storage state on disk and attached
    to the HTTP request. No browser is launched.
    """
    config: Config = ctx.obj
    access = load_access_token(config)
    refresh = load_refresh_token(config)
    if access is None or refresh is None:
        click.secho(
            "No saved session. Run `gamesheet-sdk-py login` first.",
            fg="red",
            err=True,
        )
        ctx.exit(1)

    def persist(tokens: dict[str, str]) -> None:
        save_tokens(config, **tokens)

    try:
        with AuthenticatedSession(
            config,
            access_token=access or "",
            refresh_token=refresh or "",
            on_refresh=persist,
        ) as session:
            associations = _list_associations_action(session)
    except AuthenticationError as exc:
        click.secho(f"Authentication required: {exc}", fg="red", err=True)
        ctx.exit(1)  # raises; control does not return
    except GameSheetError as exc:
        click.secho(f"GameSheet error: {exc}", fg="red", err=True)
        ctx.exit(1)  # raises; control does not return

    if output_format == "json":
        click.echo(
            json.dumps(
                [a.model_dump(mode="json") for a in associations],
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for assoc in associations:
            click.echo(f"{assoc.id}\t{assoc.title}")


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

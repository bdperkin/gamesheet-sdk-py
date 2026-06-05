"""Main CLI entry point and root command group.

This module provides the top-level ``gamesheet-sdk-py`` command-line interface.
The :func:`cli` function is the root click group that all resource-based subcommands
attach to, and :func:`main` is the entry-point wrapper that returns an integer exit
code for the package's console script.

Examples
--------
Basic usage (show help)::

    $ gamesheet-sdk-py --help

Login to GameSheet::

    $ gamesheet-sdk-py login

List associations with verbose logging::

    $ gamesheet-sdk-py -v associations list

Show browser window during headless operations::

    $ gamesheet-sdk-py --no-headless login
"""

from __future__ import annotations

import sys
from typing import Any

import click

from gamesheet_sdk import __version__
from gamesheet_sdk.cli.commands import (
    associations_group,
    completion_command,
    divisions_group,
    ipad_keys_group,
    leagues_group,
    login_command,
    referees_group,
    season_group,
    seasons_group,
    teams_group,
)
from gamesheet_sdk.cli.core import _configure_logging, resolve_exit
from gamesheet_sdk.config import Config


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, prog_name="gamesheet-sdk-py")
@click.option(
    "--base-url",
    envvar="GAMESHEET_BASE_URL",
    help="GameSheet base URL (default: https://gamesheet.app).",
)
@click.option(
    "--no-headless",
    is_flag=True,
    help="Show the browser window when running Playwright flows.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase logging verbosity (-v = INFO, -vv = DEBUG).",
)
@click.pass_context
def cli(
    ctx: click.Context,
    base_url: str | None,
    *,
    no_headless: bool,
    verbose: int,
) -> None:
    """Unofficial SDK for the GameSheet platform."""
    _configure_logging(verbose)
    overrides: dict[str, Any] = {}
    if base_url is not None:

        overrides["base_url"] = base_url
    if no_headless:

        overrides["browser_headless"] = False
    ctx.obj = Config(**overrides)
    # If no subcommand was provided, show help
    if ctx.invoked_subcommand is None:

        click.echo(ctx.get_help())


# Register all command groups and commands
cli.add_command(login_command)
cli.add_command(completion_command)
cli.add_command(associations_group)
cli.add_command(leagues_group)
cli.add_command(seasons_group)
cli.add_command(season_group)
cli.add_command(divisions_group)
cli.add_command(teams_group)
cli.add_command(referees_group)
cli.add_command(ipad_keys_group)


def main(argv: list[str] | None = None) -> int:
    """Entry-point wrapper for the gamesheet-sdk-py console script.

    Invokes the :func:`cli` click group with ``standalone_mode=False`` so that
    click's control-flow exceptions:
        * :exc:`click.exceptions.Exit`
        * :exc:`click.exceptions.UsageError`
        * :exc:`click.exceptions.Abort`
    are converted to integer exit codes rather than triggering ``sys.exit()``
    calls.  This preserves the ``main(argv) -> int`` contract expected by test
    harnesses and allows the caller to control process exit.

    :param argv: Optional command-line arguments to parse. If ``None``, defaults to ``sys.argv[1:]`` (click's
        standard behavior).
    :type argv: list[str] | None
    :returns: Exit code. 0 indicates success, non-zero indicates failure.
    :rtype: int
    """
    try:
        cli.main(args=argv, prog_name="gamesheet-sdk-py", standalone_mode=False)
    except (  # pragma: no cover - exception handling
        click.exceptions.Exit,
        click.exceptions.UsageError,
        click.exceptions.Abort,
        SystemExit,
    ) as exc:
        return resolve_exit(exc)

    return 0


if __name__ == "__main__":  # pragma: no cover

    sys.exit(main())

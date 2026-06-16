"""Main CLI entry point and root command group.

This module provides the top-level ``gamesheet-sdk-py`` command-line interface. The :func:`cli` function is
the root click group that all resource-based subcommands attach to, and :func:`main` is the entry-point
wrapper that returns an integer exit code for the package's console script.

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
from typing import TYPE_CHECKING, Any

import rich_click as click
from click.exceptions import Abort, Exit, UsageError

from gamesheet_sdk import __version__
from gamesheet_sdk.cli.commands import (
    associations_group,
    completion_command,
    divisions_group,
    games_group,
    ipad_keys_group,
    leagues_group,
    login_command,
    referees_group,
    roster_group,
    seasons_group,
    teams_group,
)
from gamesheet_sdk.cli.core import _configure_logging, resolve_exit
from gamesheet_sdk.config import Config

if TYPE_CHECKING:
    from rich_click import Context
# Configure rich-click for attractive help output
click.rich_click.TEXT_MARKUP = "rich"  # Use rich markup (replaces USE_RICH_MARKUP and USE_MARKDOWN)
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = ""
click.rich_click.MAX_WIDTH = 100
# Use new options_table configuration (replaces SHOW_METAVARS_COLUMN and APPEND_METAVARS_HELP)
click.rich_click.OPTIONS_TABLE_COLUMN_TYPES = [
    "required",
    "opt_short",
    "opt_long",
    "metavar",
    "help",
]
click.rich_click.OPTIONS_TABLE_HELP_SECTIONS = [
    "help",
    "deprecated",
    "envvar",
    "default",
    "required",
]
click.rich_click.OPTION_GROUPS = {
    "gamesheet-sdk-py": [
        {
            "name": "Configuration Options",
            "options": ["--base-url", "--no-headless"],
        },
        {
            "name": "General Options",
            "options": ["--verbose", "--version", "--help"],
        },
    ],
}
click.rich_click.COMMAND_GROUPS = {
    "gamesheet-sdk-py": [
        {
            "name": "Authentication",
            "commands": ["login", "completion"],
        },
        {
            "name": "Resource Management",
            "commands": [
                "associations",
                "leagues",
                "seasons",
                "divisions",
                "teams",
                "referees",
                "ipad-keys",
                "games",
                "roster",
            ],
        },
    ],
}


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, prog_name="gamesheet-sdk-py")
@click.option(
    "--base-url",
    envvar="GAMESHEET_BASE_URL",
    help="GameSheet base URL (default: DEFAULT_BASE_URL constant).",
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
    ctx: Context,
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
cli.add_command(divisions_group)
cli.add_command(teams_group)
cli.add_command(referees_group)
cli.add_command(ipad_keys_group)
cli.add_command(games_group)
cli.add_command(roster_group)


def main(argv: list[str] | None = None) -> int:
    """Entry-point wrapper for the gamesheet-sdk-py console script.

    Invokes the :func:`cli` click group with ``standalone_mode=False`` so that.

    click's control-flow exceptions:
        * :exc:`Exit`
        * :exc:`UsageError`
        * :exc:`Abort`
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
        Exit,
        UsageError,
        Abort,
        SystemExit,
    ) as exc:
        return resolve_exit(exc)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

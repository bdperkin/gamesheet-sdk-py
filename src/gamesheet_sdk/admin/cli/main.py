# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI entry point for the GameSheet admin dashboard.

Usage::

    gamesheet-admin --help
    gamesheet-admin login --email user@example.com
    gamesheet-admin completion bash
"""

from __future__ import annotations

import sys
from typing import Any

from click.exceptions import Abort, Exit, UsageError
import rich_click as click
from rich_click import Context

from gamesheet_sdk import __version__
from gamesheet_sdk.admin.cli.commands.associations import associations_group
from gamesheet_sdk.admin.cli.commands.completion import completion_command
from gamesheet_sdk.admin.cli.commands.divisions import divisions_group
from gamesheet_sdk.admin.cli.commands.games import games_group
from gamesheet_sdk.admin.cli.commands.ipad_keys import ipad_keys_group
from gamesheet_sdk.admin.cli.commands.leagues import leagues_group
from gamesheet_sdk.admin.cli.commands.locations import locations_group
from gamesheet_sdk.admin.cli.commands.login import login_command
from gamesheet_sdk.admin.cli.commands.referees import referees_group
from gamesheet_sdk.admin.cli.commands.roster import roster_group
from gamesheet_sdk.admin.cli.commands.seasons import seasons_group
from gamesheet_sdk.admin.cli.commands.teams import teams_group
from gamesheet_sdk.admin.cli.commands.teams_roster import register_teams_roster_group
from gamesheet_sdk.common.cli.core import _configure_logging, resolve_exit
from gamesheet_sdk.common.cli.rich_config import apply_rich_click_defaults
from gamesheet_sdk.common.config import Config

apply_rich_click_defaults()
click.rich_click.OPTION_GROUPS["gamesheet-admin"] = [
    {
        "name": "Configuration Options",
        "options": ["--base-url", "--no-headless"],
    },
    {
        "name": "General Options",
        "options": ["--verbose", "-V/--version", "--help"],
    },
]
click.rich_click.COMMAND_GROUPS["gamesheet-admin"] = [
    {
        "name": "Authentication",
        "commands": ["login"],
    },
    {
        "name": "Utilities",
        "commands": ["completion"],
    },
    {
        "name": "Resources",
        "commands": [
            "associations",
            "leagues",
            "seasons",
            "ipad-keys",
            "locations",
            "games",
            "divisions",
            "teams",
            "roster",
            "referees",
        ],
    },
]


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, "-V", "--version", prog_name="gamesheet-admin")
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
    ctx: Context,
    base_url: str | None,
    *,
    no_headless: bool,
    verbose: int,
) -> None:
    """Unofficial CLI for the GameSheet admin dashboard.

    Provides authentication, resource management, and utility commands.\f

    Args:
        ctx (Context): Click context used to store the resolved
            :class:`~gamesheet_sdk.common.config.Config`.
        base_url (str | None): Override for the GameSheet base URL, or
            ``None`` to use the default.
        no_headless (bool): When ``True``, show the browser window
            during Playwright flows.
        verbose (int): Logging verbosity level (0 = WARNING, 1 = INFO, 2
            = DEBUG).
    """
    _configure_logging(verbose)
    overrides: dict[str, Any] = {}
    if base_url is not None:
        overrides["base_url"] = base_url
    if no_headless:
        overrides["browser_headless"] = False
    ctx.obj = Config(**overrides)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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
cli.add_command(locations_group)
cli.add_command(roster_group)
register_teams_roster_group(teams_group)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``gamesheet-admin`` console script.

    Args:
        argv (list[str] | None): Command-line arguments, or ``None`` to
            use ``sys.argv``.

    Returns:
        int: Process exit code.
    """
    try:
        result = cli.main(
            args=argv,
            prog_name="gamesheet-admin",
            standalone_mode=False,
        )
    except (KeyboardInterrupt, SystemExit, Exit, UsageError, Abort) as exc:
        return resolve_exit(exc)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main())

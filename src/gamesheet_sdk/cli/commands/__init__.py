"""CLI command modules."""

from __future__ import annotations

from gamesheet_sdk.cli.commands.associations import associations_group
from gamesheet_sdk.cli.commands.completion import completion_command
from gamesheet_sdk.cli.commands.ipad_keys import ipad_keys_group
from gamesheet_sdk.cli.commands.leagues import leagues_group
from gamesheet_sdk.cli.commands.login import login_command
from gamesheet_sdk.cli.commands.season import season_group
from gamesheet_sdk.cli.commands.seasons import seasons_group

__all__ = [
    "associations_group",
    "completion_command",
    "ipad_keys_group",
    "leagues_group",
    "login_command",
    "season_group",
    "seasons_group",
]

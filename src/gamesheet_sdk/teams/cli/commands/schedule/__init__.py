# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule CLI commands for GameSheet teams."""

from gamesheet_sdk.teams.cli.commands.schedule.events import (
    events_create_command,
    events_delete_command,
    events_get_command,
    events_group,
    events_list_command,
    events_update_command,
)
from gamesheet_sdk.teams.cli.commands.schedule.games import (
    games_create_command,
    games_delete_command,
    games_get_command,
    games_group,
    games_list_command,
    games_update_command,
)
from gamesheet_sdk.teams.cli.commands.schedule.main import (
    schedule_delete_command,
    schedule_export_command,
    schedule_get_command,
    schedule_group,
    schedule_list_command,
    schedule_subscribe_command,
    schedule_update_command,
)
from gamesheet_sdk.teams.cli.commands.schedule.practices import (
    practices_create_command,
    practices_delete_command,
    practices_get_command,
    practices_group,
    practices_list_command,
    practices_update_command,
)
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)

__all__ = [
    "build_authenticated_session",
    "events_create_command",
    "events_delete_command",
    "events_get_command",
    "events_group",
    "events_list_command",
    "events_update_command",
    "games_create_command",
    "games_delete_command",
    "games_get_command",
    "games_group",
    "games_list_command",
    "games_update_command",
    "practices_create_command",
    "practices_delete_command",
    "practices_get_command",
    "practices_group",
    "practices_list_command",
    "practices_update_command",
    "run_action_or_exit",
    "schedule_delete_command",
    "schedule_export_command",
    "schedule_get_command",
    "schedule_group",
    "schedule_list_command",
    "schedule_subscribe_command",
    "schedule_update_command",
]

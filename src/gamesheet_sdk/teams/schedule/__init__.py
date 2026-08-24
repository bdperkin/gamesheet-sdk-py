# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule and calendar data from the teams API.

The ``GET /api/calendar`` endpoint returns calendar events, games, and practices for a specified team.
The ``GET /api/calendar/occurrences/{id}`` endpoint returns detailed event occurrence data.
The ``GET /api/availability/batch`` endpoint returns player/coach availability for an event.
"""

from gamesheet_sdk.teams.schedule.constants import DAY_NAME_MAP
from gamesheet_sdk.teams.schedule.create import (
    build_rrule,
    create_calendar_event_raw,
    create_event,
    create_game,
    create_practice,
    create_schedule_game_raw,
    validate_game_type,
)
from gamesheet_sdk.teams.schedule.delete import (
    delete_calendar_event,
    delete_calendar_event_raw,
    delete_calendar_occurrence,
    delete_calendar_occurrence_raw,
    delete_event,
    delete_game,
    delete_practice,
    delete_schedule_game_raw,
)
from gamesheet_sdk.teams.schedule.models import (
    CalendarEventCreated,
    CalendarSubscription,
    CreatedGameResult,
    ScheduleDeleteResult,
    ScheduleEvent,
    ScheduleEventDetail,
    UpdatedGameResult,
)
from gamesheet_sdk.teams.schedule.query import (
    _fetch_and_normalize_game_dict,
    _fetch_and_verify_occurrence_dict,
    _resolve_availability_event_id,
    _resolve_effective_team_id,
    fetch_availability_raw,
    fetch_calendar_raw,
    fetch_event_occurrence_raw,
    fetch_scheduled_game_raw,
    get_calendar_subscription,
    get_event,
    get_game,
    get_practice,
    get_schedule_event,
    list_events,
    list_games,
    list_practices,
    list_schedule,
)
from gamesheet_sdk.teams.schedule.update import (
    update_calendar_occurrence,
    update_calendar_occurrence_raw,
    update_event,
    update_game,
    update_practice,
    update_schedule_game_raw,
)

# pylint: disable=duplicate-code
__all__ = [
    "DAY_NAME_MAP",
    "CalendarEventCreated",
    "CalendarSubscription",
    "CreatedGameResult",
    "ScheduleDeleteResult",
    "ScheduleEvent",
    "ScheduleEventDetail",
    "UpdatedGameResult",
    "_fetch_and_normalize_game_dict",
    "_fetch_and_verify_occurrence_dict",
    "_resolve_availability_event_id",
    "_resolve_effective_team_id",
    "build_rrule",
    "create_calendar_event_raw",
    "create_event",
    "create_game",
    "create_practice",
    "create_schedule_game_raw",
    "delete_calendar_event",
    "delete_calendar_event_raw",
    "delete_calendar_occurrence",
    "delete_calendar_occurrence_raw",
    "delete_event",
    "delete_game",
    "delete_practice",
    "delete_schedule_game_raw",
    "fetch_availability_raw",
    "fetch_calendar_raw",
    "fetch_event_occurrence_raw",
    "fetch_scheduled_game_raw",
    "get_calendar_subscription",
    "get_event",
    "get_game",
    "get_practice",
    "get_schedule_event",
    "list_events",
    "list_games",
    "list_practices",
    "list_schedule",
    "update_calendar_occurrence",
    "update_calendar_occurrence_raw",
    "update_event",
    "update_game",
    "update_practice",
    "update_schedule_game_raw",
    "validate_game_type",
]
# pylint: enable=duplicate-code

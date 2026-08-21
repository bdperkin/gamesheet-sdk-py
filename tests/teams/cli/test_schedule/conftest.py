# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared test fixtures and helpers for schedule CLI tests."""

from __future__ import annotations

import pytest

from gamesheet_sdk.teams.schedule import ScheduleEvent


@pytest.fixture
def sample_events() -> list[ScheduleEvent]:
    """Return sample ScheduleEvent objects for CLI tests.

    Returns:
        list[ScheduleEvent]: List of sample ScheduleEvent objects.

    """
    return [
        ScheduleEvent(
            id="evt-101",
            type="event",
            eventDate="2026-08-20",
            eventTime="17:00",
            eventTitle="Team Pizza Party",
            eventLocation="Clubhouse",
        ),
        ScheduleEvent(
            id=202,
            type="game",
            eventDate="2026-08-22",
            eventTime="19:00",
            eventTitle="Hawks vs Eagles",
            eventLocation="Arena A",
        ),
        ScheduleEvent(
            id="prac-303",
            type="practice",
            eventDate="2026-08-24",
            eventTime="06:00",
            eventTitle="Morning Skate",
            eventLocation="Rink 2",
        ),
    ]


def get_sample_events() -> list[ScheduleEvent]:
    """Return sample ScheduleEvent objects directly without fixture.

    Returns:
        list[ScheduleEvent]: List of sample ScheduleEvent objects.

    """
    return [
        ScheduleEvent(
            id="evt-101",
            type="event",
            eventDate="2026-08-20",
            eventTime="17:00",
            eventTitle="Team Pizza Party",
            eventLocation="Clubhouse",
        ),
        ScheduleEvent(
            id=202,
            type="game",
            eventDate="2026-08-22",
            eventTime="19:00",
            eventTitle="Hawks vs Eagles",
            eventLocation="Arena A",
        ),
        ScheduleEvent(
            id="prac-303",
            type="practice",
            eventDate="2026-08-24",
            eventTime="06:00",
            eventTitle="Morning Skate",
            eventLocation="Rink 2",
        ),
    ]

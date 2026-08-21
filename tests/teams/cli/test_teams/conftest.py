# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures and mock data for teams CLI tests."""

from __future__ import annotations

from gamesheet_sdk.teams.teams import (
    TeamDetail,
    TeamSummary,
)

MOCK_SUMMARIES = [
    TeamSummary(
        memberId="m-101",
        teamId="t-201",
        relationship="coach",
        status="active",
        onboardingCompletedAt="2024-09-01T00:00:00Z",
        teamName="Hawks 12U",
        ageCategory="12U",
        clubId="c-301",
        joinedAt="2024-08-15T00:00:00Z",
        statsYear="2024-2025",
    ),
    TeamSummary(
        memberId="m-102",
        teamId="t-202",
        relationship="manager",
        status="active",
        onboardingCompletedAt="2024-09-02T00:00:00Z",
        teamName="Eagles 14U",
        ageCategory="14U",
        clubId="c-302",
        joinedAt="2024-08-20T00:00:00Z",
        statsYear="2024-2025",
    ),
]

MOCK_DETAIL = TeamDetail(
    memberId="m-101",
    teamId="t-201",
    relationship="coach",
    status="active",
    onboardingCompletedAt="2024-09-01T00:00:00Z",
    teamName="Hawks 12U",
    ageCategory="12U",
    clubId="c-301",
    joinedAt="2024-08-15T00:00:00Z",
    statsYear="2024-2025",
)

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Test endpoint URL builders for common API patterns.

This module provides helper functions to construct frequently-used test endpoint URLs, reducing duplication
and making tests more maintainable.
"""

from __future__ import annotations

from tests.helpers.constants import TEST_BASE_URL


def coaches_endpoint(season_id: str) -> str:
    """Build the coaches endpoint URL for a season.

    :param season_id: Season identifier.
    :type season_id: str
    :returns: Full endpoint URL.
    :rtype: str
    """
    return f"{TEST_BASE_URL}/api/seasons/{season_id}/coaches"


def players_endpoint(season_id: str) -> str:
    """Build the players endpoint URL for a season.

    :param season_id: Season identifier.
    :type season_id: str
    :returns: Full endpoint URL.
    :rtype: str
    """
    return f"{TEST_BASE_URL}/api/seasons/{season_id}/players"


def referees_endpoint(season_id: str) -> str:
    """Build the referees endpoint URL for a season.

    :param season_id: Season identifier.
    :type season_id: str
    :returns: Full endpoint URL.
    :rtype: str
    """
    return f"{TEST_BASE_URL}/api/seasons/{season_id}/referees"


def referee_endpoint(season_id: str, referee_id: str) -> str:
    """Build the single referee endpoint URL.

    :param season_id: Season identifier.
    :type season_id: str
    :param referee_id: Referee identifier.
    :type referee_id: str
    :returns: Full endpoint URL.
    :rtype: str
    """
    return f"{TEST_BASE_URL}/api/seasons/{season_id}/referees/{referee_id}"


def teams_endpoint(season_id: str) -> str:
    """Build the teams endpoint URL for a season.

    :param season_id: Season identifier.
    :type season_id: str
    :returns: Full endpoint URL.
    :rtype: str
    """
    return f"{TEST_BASE_URL}/api/seasons/{season_id}/teams"


def team_endpoint(season_id: str, team_id: str) -> str:
    """Build the single team endpoint URL.

    :param season_id: Season identifier.
    :type season_id: str
    :param team_id: Team identifier.
    :type team_id: str
    :returns: Full endpoint URL.
    :rtype: str
    """
    return f"{TEST_BASE_URL}/api/seasons/{season_id}/teams/{team_id}"

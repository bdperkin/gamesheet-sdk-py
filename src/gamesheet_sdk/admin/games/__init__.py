# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet games: scheduled, completed, and bracket games within a season.

Games represent matchups between teams. This module provides access to three game views:

- **Scheduled games:** Upcoming/future games (CRUD operations)
- **Completed games:** Finished games with results
- **Bracket games:** Playoff/tournament games

The games data is retrieved from the BFF (Backend For Frontend) API at the ``/games-list/v1`` endpoint with
various filter parameters.

For scheduled game mutations (create/update/delete), the JSON:API-style ``/api/seasons/{id}/schedule``
endpoint is used.
"""

from __future__ import annotations

from gamesheet_sdk.admin.games.brackets import get_game, list_brackets, list_completed
from gamesheet_sdk.admin.games.broadcasters import (
    list_broadcasters,
    validate_broadcaster_key,
)
from gamesheet_sdk.admin.games.completed import (
    download_completed_game_pdf,
    get_completed_game,
)
from gamesheet_sdk.admin.games.helpers import validate_game_type
from gamesheet_sdk.admin.games.locations import (
    get_location,
    list_locations,
    validate_location,
)
from gamesheet_sdk.admin.games.models import (
    Broadcaster,
    Game,
    GameData,
    Location,
    Relationship,
    RelationshipData,
    ScheduledGame,
    ScheduledGameAttributes,
    ScheduledGameData,
    ScheduledGameRelationships,
    Scorekeeper,
    TeamInfo,
)
from gamesheet_sdk.admin.games.scheduled import (
    create_scheduled_game,
    delete_scheduled_game,
    get_scheduled_game,
    list_scheduled,
    update_scheduled_game,
)

__all__ = [
    # Models
    "Broadcaster",
    "Game",
    "GameData",
    "Location",
    "Relationship",
    "RelationshipData",
    "ScheduledGame",
    "ScheduledGameAttributes",
    "ScheduledGameData",
    "ScheduledGameRelationships",
    "Scorekeeper",
    "TeamInfo",
    # Scheduled operations
    "create_scheduled_game",
    "delete_scheduled_game",
    # Completed operations
    "download_completed_game_pdf",
    "get_completed_game",
    # Bracket/list operations
    "get_game",
    # Location operations
    "get_location",
    "get_scheduled_game",
    "list_brackets",
    # Broadcaster operations
    "list_broadcasters",
    "list_completed",
    "list_locations",
    "list_scheduled",
    "update_scheduled_game",
    "validate_broadcaster_key",
    # Helpers
    "validate_game_type",
    "validate_location",
]

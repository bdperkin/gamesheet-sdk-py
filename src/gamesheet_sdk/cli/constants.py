# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI constants for reusable click.Choice options."""

# Player positions
PLAYER_POSITIONS = [
    "Forward",
    "Left Wing",
    "Right Wing",
    "Centre",
    "Pusher (Sled)",
    "Defence",
    "Goalie",
]
# Player status options
PLAYER_STATUS = ["Regular", "Affiliated"]
# Player designation options
PLAYER_DESIGNATION = ["Captain", "Alternate Captain"]
# Coach positions
COACH_POSITIONS = [
    "Head Coach",
    "Assistant Coach",
    "Head Coach at Large",
    "Assistant Coach at Large",
    "Assistant Trainer",
    "Manager",
    "Trainer",
    "Trainer at Large",
]
# Season status options
SEASON_STATUS = ["archived", "active", "all"]
# Shell types for completion
SHELL_TYPES = ["bash", "zsh", "fish"]

# CLI command name and common command strings
CLI_COMMAND_NAME = "gamesheet-sdk-py"
CLI_COMMAND_LOGIN = "gamesheet-sdk-py login"

# Help text fragments
HELP_AUTH_REQUIRED = "Requires authentication (run 'gamesheet-sdk-py login' first)."
HELP_CASE_INSENSITIVE = "(case-insensitive)"
HELP_VALIDATED_AGAINST_API = "Validated against API"
HELP_OPTIONAL = "(optional)"
HELP_DESTRUCTIVE_OPERATION = (
    "This operation is destructive and requires confirmation unless --force is specified."
)

# ISO 8601 format examples and help text
ISO_8601_FORMAT_EXAMPLE = "2026-07-04T12:00:00Z"
ISO_8601_HELP_TEXT = f"ISO 8601 format, e.g., {ISO_8601_FORMAT_EXAMPLE}"

# Flexible datetime help text
FLEXIBLE_DATETIME_HELP = (
    "Flexible date/time format (e.g., '2026-07-04 7:00pm', "
    "'July 4 2026 19:00', '2026-07-04T19:00:00-04:00'). "
    "If no timezone is specified, the system timezone is used."
)
DURATION_HELP = "Game duration in positive minutes."
SPLIT_DATE_HELP = "Date component (e.g., '2026-07-04', 'July 4 2026')."
SPLIT_TIME_HELP = "Time component (e.g., '7:00pm', '19:00')."

# IANA timezone examples
IANA_TIMEZONE_EXAMPLE = "America/New_York"
IANA_TIMEZONE_HELP_TEXT = f"IANA time zone name (e.g., {IANA_TIMEZONE_EXAMPLE})"

# Time zone offset examples
TIMEZONE_OFFSET_EXAMPLE = "-240"
TIMEZONE_OFFSET_HELP_TEXT = f"Time zone offset in minutes (e.g., {TIMEZONE_OFFSET_EXAMPLE} for EDT)"

# Common CLI help snippets
HELP_USE_LOCATIONS_LIST = "Use 'gamesheet-sdk-py locations list' to see all valid locations."
# Re-export from shared.constants to avoid circular imports (used in errors.py)
# pylint: disable-next=unused-import,wrong-import-position
from gamesheet_sdk.shared.constants import HELP_USE_SEASONS_LIST  # noqa: E402, F401

HELP_USE_BROADCASTERS_LIST = "Use 'gamesheet-sdk-py games broadcasters list' to see valid options."

# Resource ID help text for Click options
HELP_SEASON_ID_FOR_TEAM = "Season ID containing the team."
HELP_SEASON_ID_FOR_REFEREE = "Season ID containing the referee."
HELP_SEASON_ID_FOR_DIVISION = "Season ID containing the division."

# Update operation help text for Click options
HELP_UPDATED_EXTERNAL_ID = "Updated external identifier."
HELP_UPDATED_FIRST_NAME = "Updated first name."
HELP_UPDATED_LAST_NAME = "Updated last name."

# Create operation help text for Click options (person names)
HELP_COACH_FIRST_NAME = "Coach's first name."
HELP_COACH_LAST_NAME = "Coach's last name."
HELP_PLAYER_FIRST_NAME = "Player's first name."
HELP_PLAYER_LAST_NAME = "Player's last name."
HELP_REFEREE_FIRST_NAME = "Referee's first name."
HELP_REFEREE_LAST_NAME = "Referee's last name."

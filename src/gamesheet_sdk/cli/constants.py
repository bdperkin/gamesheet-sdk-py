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

# IANA timezone examples
IANA_TIMEZONE_EXAMPLE = "America/New_York"
IANA_TIMEZONE_HELP_TEXT = f"IANA time zone name (e.g., {IANA_TIMEZONE_EXAMPLE})"

# Time zone offset examples
TIMEZONE_OFFSET_EXAMPLE = "-240"
TIMEZONE_OFFSET_HELP_TEXT = f"Time zone offset in minutes (e.g., {TIMEZONE_OFFSET_EXAMPLE} for EDT)"

# Common CLI help snippets
HELP_USE_LOCATIONS_LIST = "Use 'gamesheet-sdk-py locations list' to see all valid locations."
HELP_USE_SEASONS_LIST = (
    "To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>"
)
HELP_USE_BROADCASTERS_LIST = (
    "Use 'gamesheet-sdk-py games broadcasters list' to see valid options."
)

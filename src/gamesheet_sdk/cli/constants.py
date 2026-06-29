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

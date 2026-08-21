# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Constants for teams schedule module."""

from __future__ import annotations

DAY_NAME_MAP: dict[str, str] = {
    "mo": "MO",
    "mon": "MO",
    "monday": "MO",
    "tu": "TU",
    "tue": "TU",
    "tues": "TU",
    "tuesday": "TU",
    "we": "WE",
    "wed": "WE",
    "wednesday": "WE",
    "th": "TH",
    "thu": "TH",
    "thurs": "TH",
    "thursday": "TH",
    "fr": "FR",
    "fri": "FR",
    "friday": "FR",
    "sa": "SA",
    "sat": "SA",
    "saturday": "SA",
    "su": "SU",
    "sun": "SU",
    "sunday": "SU",
}

__all__ = ["DAY_NAME_MAP"]

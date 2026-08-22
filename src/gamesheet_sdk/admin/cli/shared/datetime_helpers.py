# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Backwards-compatible re-export of the shared datetime helpers.

The implementations moved to :mod:`gamesheet_sdk.common.cli.datetime_helpers` so that the ``common`` pillar
no longer imports from ``admin``; that inversion made ``common.cli.game_times`` unimportable from the teams
CLI. This module is kept so existing ``admin.cli.shared`` imports keep working.
"""

from __future__ import annotations

from gamesheet_sdk.common.cli.datetime_helpers import (
    MIN_REQUIRED_INPUTS,
    _format_utc_iso,
    _resolve_all_three,
    _resolve_end_and_duration,
    _resolve_single_update,
    _resolve_start_and_duration,
    _resolve_start_and_end,
    _resolve_with_all_inputs,
    get_local_timezone_name,
    get_local_timezone_offset,
    parse_flexible_datetime,
    resolve_create_times,
    resolve_datetime_input,
    resolve_update_times,
    validate_end_after_start,
    validate_no_input_conflict,
)

__all__ = [
    "MIN_REQUIRED_INPUTS",
    "_format_utc_iso",
    "_resolve_all_three",
    "_resolve_end_and_duration",
    "_resolve_single_update",
    "_resolve_start_and_duration",
    "_resolve_start_and_end",
    "_resolve_with_all_inputs",
    "get_local_timezone_name",
    "get_local_timezone_offset",
    "parse_flexible_datetime",
    "resolve_create_times",
    "resolve_datetime_input",
    "resolve_update_times",
    "validate_end_after_start",
    "validate_no_input_conflict",
]

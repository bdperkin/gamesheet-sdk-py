# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared CLI utilities."""

from __future__ import annotations

from gamesheet_sdk.admin.cli.shared.datetime_helpers import (
    get_local_timezone_name,
    get_local_timezone_offset,
    parse_flexible_datetime,
    resolve_create_times,
    resolve_datetime_input,
    resolve_update_times,
    validate_end_after_start,
    validate_no_input_conflict,
)
from gamesheet_sdk.admin.cli.shared.decorators import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    player_update_options,
    team_create_options,
    team_update_options,
)
from gamesheet_sdk.admin.cli.shared.rendering import (
    render_get_command,
    render_list_command,
    render_penalty_report,
)

__all__ = [
    "common_output_options",
    "get_fields_option",
    "get_local_timezone_name",
    "get_local_timezone_offset",
    "list_columns_option",
    "parse_flexible_datetime",
    "player_update_options",
    "render_get_command",
    "render_list_command",
    "render_penalty_report",
    "resolve_create_times",
    "resolve_datetime_input",
    "resolve_update_times",
    "team_create_options",
    "team_update_options",
    "validate_end_after_start",
    "validate_no_input_conflict",
]

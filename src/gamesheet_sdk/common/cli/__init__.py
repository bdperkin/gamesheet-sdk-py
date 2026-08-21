# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared CLI utilities for GameSheet CLIs."""

from gamesheet_sdk.common.cli.core import (
    ResourceGroup,
    _configure_logging,
    _should_color,
    confirm_destructive,
    parse_columns_spec,
    resolve_exit,
    resolve_system_exit,
)
from gamesheet_sdk.common.cli.datetime_helpers import (
    MIN_REQUIRED_INPUTS,
    get_local_timezone_name,
    get_local_timezone_offset,
    parse_flexible_datetime,
    resolve_create_times,
    resolve_datetime_input,
    resolve_update_times,
    validate_end_after_start,
    validate_no_input_conflict,
)
from gamesheet_sdk.common.cli.decorators import (
    columns_option,
    common_output_options,
)
from gamesheet_sdk.common.cli.helpers import run_action_or_exit
from gamesheet_sdk.common.cli.rendering import (
    render_get_command,
    render_list_command,
    render_penalty_report,
)

__all__ = [
    "MIN_REQUIRED_INPUTS",
    "ResourceGroup",
    "_configure_logging",
    "_should_color",
    "columns_option",
    "common_output_options",
    "confirm_destructive",
    "get_local_timezone_name",
    "get_local_timezone_offset",
    "parse_columns_spec",
    "parse_flexible_datetime",
    "render_get_command",
    "render_list_command",
    "render_penalty_report",
    "resolve_create_times",
    "resolve_datetime_input",
    "resolve_exit",
    "resolve_system_exit",
    "resolve_update_times",
    "run_action_or_exit",
    "validate_end_after_start",
    "validate_no_input_conflict",
]

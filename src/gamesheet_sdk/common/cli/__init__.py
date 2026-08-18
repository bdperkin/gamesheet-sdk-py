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
from gamesheet_sdk.common.cli.decorators import (
    common_output_options,
    get_fields_option,
    list_columns_option,
)
from gamesheet_sdk.common.cli.helpers import run_action_or_exit
from gamesheet_sdk.common.cli.rendering import (
    render_get_command,
    render_list_command,
    render_penalty_report,
)

__all__ = [
    "ResourceGroup",
    "_configure_logging",
    "_should_color",
    "common_output_options",
    "confirm_destructive",
    "get_fields_option",
    "list_columns_option",
    "parse_columns_spec",
    "render_get_command",
    "render_list_command",
    "render_penalty_report",
    "resolve_exit",
    "resolve_system_exit",
    "run_action_or_exit",
]

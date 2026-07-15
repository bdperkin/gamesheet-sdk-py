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

__all__ = [
    "ResourceGroup",
    "_configure_logging",
    "_should_color",
    "confirm_destructive",
    "parse_columns_spec",
    "resolve_exit",
    "resolve_system_exit",
]

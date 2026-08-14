# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared Rich logging configuration for CLI tools."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.logging import RichHandler

if TYPE_CHECKING:
    from rich.console import Console


def configure_logging(log_level: str, console: Console) -> None:
    """Configure the root logger with a Rich handler.

    Args:
        log_level (str): One of 'debug', 'info', 'warning', 'error'.
        console (Console): Rich Console instance for output.

    """
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )

    logging.basicConfig(
        level=level_map[log_level],
        format="%(message)s",
        handlers=[handler],
        force=True,
    )

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared Rich logging configuration for CLI tools."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler


def configure_logging(log_level: str, console: Console) -> None:
    """Configure the root logger with a Rich handler.

    :param log_level: One of 'debug', 'info', 'warning', 'error'.
    :type log_level: str
    :param console: Rich Console instance for output.
    :type console: Console
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

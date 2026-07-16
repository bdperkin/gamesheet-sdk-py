# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared rich-click configuration for all GameSheet CLIs."""

from __future__ import annotations

import rich_click as click


def apply_rich_click_defaults() -> None:
    """Apply common rich-click display settings.

    Sets text markup, argument display, error styling, column layout, and help section ordering. Both
    ``gamesheet-admin`` and ``gamesheet-teams`` call this at module level so every CLI gets a consistent look-
    and-feel.
    """
    click.rich_click.TEXT_MARKUP = "rich"
    click.rich_click.SHOW_ARGUMENTS = True
    click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
    click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
    click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
    click.rich_click.ERRORS_EPILOGUE = ""
    click.rich_click.MAX_WIDTH = 100
    click.rich_click.OPTIONS_TABLE_COLUMN_TYPES = [
        "required",
        "opt_short",
        "opt_long",
        "metavar",
        "help",
    ]
    click.rich_click.OPTIONS_TABLE_HELP_SECTIONS = [
        "help",
        "deprecated",
        "envvar",
        "default",
        "required",
    ]

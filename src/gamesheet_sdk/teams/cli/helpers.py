# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI helper functions for the teams dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.common.auth.tokens import (
    load_access_token,
    load_refresh_token,
    save_tokens,
)
from gamesheet_sdk.common.cli.helpers import run_action_or_exit
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config

__all__ = [
    "build_authenticated_session",
    "run_action_or_exit",
]


def build_authenticated_session(
    config: Config,
) -> TeamsAuthenticatedSession:
    """Build a TeamsAuthenticatedSession from saved tokens.

    Args:
        config (Config): The application config.

    Returns:
        TeamsAuthenticatedSession: A TeamsAuthenticatedSession ready to use.

    Raises:
        Exit: If no tokens are saved.

    """
    access = load_access_token(config)
    refresh = load_refresh_token(config)
    if access is None or refresh is None:
        click.secho(
            "No saved session found. Run `gamesheet-teams login` first.",
            fg="red",
            err=True,
        )
        raise Exit(1)

    return TeamsAuthenticatedSession(
        config,
        access_token=access,
        refresh_token=refresh,
        on_refresh=lambda tokens: save_tokens(config, **tokens),
    )

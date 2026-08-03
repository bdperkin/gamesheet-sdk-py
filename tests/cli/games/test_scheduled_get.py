# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for scheduled games get CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from tests.helpers import ASSOCIATION_ID


def test_games_scheduled_get_coverage() -> None:
    """Ensure games scheduled get command body is covered."""
    from unittest.mock import MagicMock

    from gamesheet_sdk.admin.cli.commands.games import games_group

    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.games_scheduled.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.games_scheduled.run_action_or_exit",
            return_value=MagicMock(
                model_dump=lambda **__kw: {
                    "id": 123,
                    "status": "scheduled",
                    "date": "2024-01-01",
                },
            ),
        ),
        patch("gamesheet_sdk.admin.cli.commands.games_scheduled.render_get_command"),
    ):
        result = runner.invoke(
            games_group,
            [
                "--season-id",
                "100",
                "scheduled",
                "get",
                "--game-id",
                ASSOCIATION_ID,
                "-F",
                "json",
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code

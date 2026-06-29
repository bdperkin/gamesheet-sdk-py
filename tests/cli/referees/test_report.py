# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for referees report command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli
from gamesheet_sdk.referees import RefereeReport
from tests.helpers import (
    REFEREE_EXTERNAL_ID_TERTIARY,
    SEASON_ID,
)


def test_referees_report_with_all_fields(runner: CliRunner) -> None:
    """The referees report command should retrieve a comprehensive report."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.referees._get_referee_report_action",
        ) as mock_report,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_report.return_value = RefereeReport(
            external_id=REFEREE_EXTERNAL_ID_TERTIARY,
            first_name="WES",
            last_name="MCCAULEY",
            games_refereed=15,
            average_pim_per_game=4.2,
            most_frequent_penalty="Tripping",
            major_penalties_count=3,
            games=[
                {"id": "game1", "date": "2026-01-15"},
                {"id": "game2", "date": "2026-01-22"},
            ],
            major_penalties=[
                {"player": "Smith", "penalty": "Fighting"},
                {"player": "Jones", "penalty": "Checking from Behind"},
            ],
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "report",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146198",
            ],
        )
        assert not result.exit_code
        mock_report.assert_called_once()
        args = mock_report.call_args[0]
        assert args[1] == SEASON_ID
        assert args[2] == "1146198"


def test_referees_report_missing_referee_id_shows_error(runner: CliRunner) -> None:
    """Calling 'referees report' without referee ID should show an error."""
    result = runner.invoke(
        cli,
        [
            "referees",
            "report",
            "--season-id",
            SEASON_ID,
        ],
    )
    assert result.exit_code == 2
    assert "referee-id" in result.output.lower() or "missing option" in result.output.lower()


def test_referees_report_json_output(runner: CliRunner) -> None:
    """The referees report command should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.referees._get_referee_report_action",
        ) as mock_report,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_report.return_value = RefereeReport(
            external_id="TEST-EXTERNAL-ID",
            first_name="Test",
            last_name="Referee",
            games_refereed=5,
            average_pim_per_game=2.5,
            most_frequent_penalty="Hooking",
            major_penalties_count=1,
            games=[],
            major_penalties=[],
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "report",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146199",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert '"external_id": "TEST-EXTERNAL-ID"' in result.output
        assert '"first_name": "Test"' in result.output
        assert '"games_refereed": 5' in result.output

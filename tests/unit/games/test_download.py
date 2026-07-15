# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for download_completed_game_pdf function."""

from __future__ import annotations

from pathlib import Path

import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.admin.games import download_completed_game_pdf
from gamesheet_sdk.common.constants import DEFAULT_BASE_URL, SCORESHEET_SERVICE_BASE_URL
from tests.fixtures.constants import TEST_BEARER_TOKEN


@responses.activate
def test_download_completed_game_pdf(tmp_path: Path) -> None:
    """Test download_completed_game_pdf function."""
    responses.add(
        responses.GET,
        f"{SCORESHEET_SERVICE_BASE_URL}/service.scoresheets/v4/get-game/game-1",
        body=b"PDF content",
        status=200,
    )
    output_file = tmp_path / "test.pdf"
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        download_completed_game_pdf(session, "game-1", str(output_file))
    assert output_file.exists()
    assert output_file.read_bytes() == b"PDF content"

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared pytest fixtures and configuration for the test suite."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from gamesheet_sdk import Config


@pytest.fixture(autouse=True)
def _clear_gamesheet_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip any ambient ``GAMESHEET_*`` env vars so every test sees defaults.

    Returns:
        None: None
    """
    for key in list(os.environ):
        if key.startswith("GAMESHEET_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """Build a Config that keeps all on-disk state inside a per-test tmp dir.

    Single shared fixture for both HTTP-session and browser-session tests; using one definition avoids the
    pylint ``duplicate-code`` warning that fires when near- identical fixtures live in two test modules.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Config: Return value.
    """
    return Config(
        base_url="https://test.example",
        session_path=tmp_path / "session.json",
        browser_state_path=tmp_path / "browser-state.json",
        request_retries=0,
        timeout=1.0,
    )


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, object]:
    """Defaults applied to every @pytest.mark.vcr test.

    Sensitive headers and body fields are scrubbed before cassettes are written, so recordings can be
    committed without leaking credentials.

    Returns:
        dict[str, object]: Dictionary of results.
    """
    return {
        "filter_headers": [
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
        ],
        "filter_query_parameters": [
            "api_key",
            "token",
            "access_token",
        ],
        "filter_post_data_parameters": [
            "password",
            "token",
            "access_token",
            "client_secret",
        ],
        "record_mode": "once",
    }


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict[str, object]:
    """Defaults for the pytest-playwright ``browser`` fixture.

    Tests opt in to a real browser by adding @pytest.mark.browser and requesting the ``page`` / ``context`` /
    ``browser`` fixtures from pytest-playwright. They are skipped via ``pytest -m 'not browser'``.

    Returns:
        dict[str, object]: Dictionary of results.
    """
    return {"headless": True}

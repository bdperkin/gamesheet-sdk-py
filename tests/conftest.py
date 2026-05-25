"""Shared pytest fixtures and configuration for the test suite."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, object]:
    """Defaults applied to every @pytest.mark.vcr test.

    Sensitive headers and body fields are scrubbed before cassettes are
    written, so recordings can be committed without leaking credentials.
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
    """Defaults for the pytest-playwright `browser` fixture.

    Tests opt in to a real browser by adding @pytest.mark.browser and
    requesting the `page` / `context` / `browser` fixtures from
    pytest-playwright. They are skipped via `pytest -m 'not browser'`.
    """
    return {"headless": True}

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the HTTP-only teams login flow."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

from gamesheet_sdk import AuthenticationError, Config
from gamesheet_sdk.teams.login import TeamsLoginFlow
from tests.helpers import TEST_EMAIL_MINIMAL

if TYPE_CHECKING:
    from pydantic import SecretStr


def _firebase_ok(id_token: str = "firebase-id-tok") -> MagicMock:  # noqa: S107 # nosec B107
    """Build a mock response for a successful Firebase sign-in."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"idToken": id_token}
    return resp


def _firebase_error(
    status: int,
    body: dict[str, Any] | None = None,
) -> MagicMock:
    """Build a mock response for a failed Firebase sign-in."""
    resp = MagicMock()
    resp.status_code = status
    if body is not None:
        resp.json.return_value = body
    else:
        resp.json.side_effect = ValueError("no body")
    return resp


def _token_exchange_ok(
    access: str = "access-tok",
    refresh: str = "refresh-tok",
) -> MagicMock:
    """Build a mock response for a successful token exchange."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "success": True,
        "tokens": {"access": access, "refresh": refresh},
    }
    return resp


def _token_exchange_error(status: int) -> MagicMock:
    """Build a mock response for a failed token exchange."""
    resp = MagicMock()
    resp.status_code = status
    return resp


# ---------- happy path ---------------------------------------------------


def test_teams_login_flow_happy_path(config: Config) -> None:
    """Test that TeamsLoginFlow.authenticate returns access and refresh tokens."""
    with (
        patch(
            "gamesheet_sdk.teams.login.requests.post",
            return_value=_firebase_ok(),
        ),
        patch(
            "gamesheet_sdk.teams.login.requests.get",
            return_value=_token_exchange_ok(),
        ),
        patch("gamesheet_sdk.teams.login.save_tokens") as mock_save,
    ):
        flow = TeamsLoginFlow(config)
        tokens = flow.authenticate(
            email=TEST_EMAIL_MINIMAL,
            password="x",
            timeout=5.0,
        )

    assert tokens == {"access": "access-tok", "refresh": "refresh-tok"}
    mock_save.assert_called_once_with(
        config,
        access="access-tok",
        refresh="refresh-tok",
    )


# ---------- credential validation ----------------------------------------


def test_teams_login_flow_missing_email_raises(config: Config) -> None:
    """Test that authenticate raises when no email is available."""
    flow = TeamsLoginFlow(config)
    with pytest.raises(AuthenticationError, match="requires an email"):
        flow.authenticate(password="x")


def test_teams_login_flow_missing_password_raises(config: Config) -> None:
    """Test that authenticate raises when no password is available."""
    flow = TeamsLoginFlow(config)
    with pytest.raises(AuthenticationError, match="requires a password"):
        flow.authenticate(email=TEST_EMAIL_MINIMAL)


def test_teams_login_flow_reads_credentials_from_config() -> None:
    """Test that authenticate reads email and password from config."""
    cfg = Config(
        base_url="https://test.example",
        username="bob@example.com",
        password=cast("SecretStr", "s3cret"),
    )
    with (
        patch(
            "gamesheet_sdk.teams.login.requests.post",
            return_value=_firebase_ok(),
        ) as mock_post,
        patch(
            "gamesheet_sdk.teams.login.requests.get",
            return_value=_token_exchange_ok(),
        ),
        patch("gamesheet_sdk.teams.login.save_tokens"),
    ):
        flow = TeamsLoginFlow(cfg)
        flow.authenticate()

    call_kwargs = mock_post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    assert payload["email"] == "bob@example.com"
    assert payload["password"] == "s3cret"  # pragma: allowlist secret


# ---------- firebase failures --------------------------------------------


@pytest.mark.parametrize(
    "firebase_message",
    [
        "EMAIL_NOT_FOUND",
        "INVALID_LOGIN_CREDENTIALS",
        "USER_DISABLED",
        "TOO_MANY_ATTEMPTS_TRY_LATER",
    ],
)
def test_teams_login_flow_surfaces_firebase_error(
    config: Config,
    firebase_message: str,
) -> None:
    """Test that Firebase error codes are included in the raised exception."""
    with patch(
        "gamesheet_sdk.teams.login.requests.post",
        return_value=_firebase_error(
            400,
            {"error": {"code": 400, "message": firebase_message}},
        ),
    ):
        flow = TeamsLoginFlow(config)
        with pytest.raises(AuthenticationError) as exc_info:
            flow.authenticate(email=TEST_EMAIL_MINIMAL, password="x")
    assert firebase_message in str(exc_info.value)
    assert "Firebase" in str(exc_info.value)


def test_teams_login_flow_firebase_non_json_error(config: Config) -> None:
    """Test that Firebase failure without parseable body shows HTTP status."""
    with patch(
        "gamesheet_sdk.teams.login.requests.post",
        return_value=_firebase_error(500),
    ):
        flow = TeamsLoginFlow(config)
        with pytest.raises(AuthenticationError) as exc_info:
            flow.authenticate(email=TEST_EMAIL_MINIMAL, password="x")
    assert "HTTP 500" in str(exc_info.value)


def test_teams_login_flow_firebase_error_non_dict_error_field(
    config: Config,
) -> None:
    """Test Firebase error with non-dict error field falls back to HTTP status."""
    with patch(
        "gamesheet_sdk.teams.login.requests.post",
        return_value=_firebase_error(403, {"error": "string-not-dict"}),
    ):
        flow = TeamsLoginFlow(config)
        with pytest.raises(AuthenticationError) as exc_info:
            flow.authenticate(email=TEST_EMAIL_MINIMAL, password="x")
    assert "HTTP 403" in str(exc_info.value)


def test_teams_login_flow_firebase_error_non_string_message(
    config: Config,
) -> None:
    """Test Firebase error with non-string message falls back to HTTP status."""
    with patch(
        "gamesheet_sdk.teams.login.requests.post",
        return_value=_firebase_error(403, {"error": {"message": 12345}}),
    ):
        flow = TeamsLoginFlow(config)
        with pytest.raises(AuthenticationError) as exc_info:
            flow.authenticate(email=TEST_EMAIL_MINIMAL, password="x")
    assert "HTTP 403" in str(exc_info.value)


# ---------- token exchange failures --------------------------------------


def test_teams_login_flow_token_exchange_failure(config: Config) -> None:
    """Test that token exchange failure raises AuthenticationError."""
    with (
        patch(
            "gamesheet_sdk.teams.login.requests.post",
            return_value=_firebase_ok(),
        ),
        patch(
            "gamesheet_sdk.teams.login.requests.get",
            return_value=_token_exchange_error(401),
        ),
    ):
        flow = TeamsLoginFlow(config)
        with pytest.raises(AuthenticationError, match="token exchange failed"):
            flow.authenticate(email=TEST_EMAIL_MINIMAL, password="x")

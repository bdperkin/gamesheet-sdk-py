"""Tests for token loading, saving, and refreshing."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    BrowserSession,
    Config,
    GameSheetError,
)
from gamesheet_sdk.auth.constants import (
    FIREBASE_AUTH_URL,
    REFRESH_URL,
    TOKEN_EXCHANGE_URL,
)
from gamesheet_sdk.auth.tokens import (
    load_access_token,
    refresh_access_token,
    save_tokens,
)


def _make_response(url: str, status: int, body: Any = None) -> MagicMock:
    """Build a MagicMock that quacks like a playwright Response."""
    r = MagicMock(name=f"response[{url}]")
    r.url = url
    r.status = status
    if body is not None:
        r.json.return_value = body
    else:
        r.json.side_effect = ValueError("no body")
    return r


_FIREBASE_URL = f"{FIREBASE_AUTH_URL}?key=X"
_TOKEN_URL = TOKEN_EXCHANGE_URL  # nosec B105


@pytest.fixture
def fake_browser_session(config: Config) -> MagicMock:
    """A BrowserSession-spec'd mock whose page captures a response listener.

    The page's ``click`` is wired to fire whatever responses the test has staged via the ``staged_responses``
    attribute; the test sets that list to control what arrives after submit.
    """
    sess = MagicMock(spec=BrowserSession)
    sess.config = config
    page = MagicMock(name="page")
    sess.goto.return_value = page
    # Capture the response callback the production code registers.
    listeners: dict[str, Any] = {}

    def register(event: str, callback: Any) -> None:
        listeners[event] = callback

    page.on.side_effect = register
    # Default: no staged responses (simulates timeout).
    page.staged_responses = []

    def click(_selector: str) -> None:
        for response in page.staged_responses:
            listeners["response"](response)

    page.click.side_effect = click
    # Make wait_for_timeout actually advance the clock a little so loops
    # don't spin entirely in zero real time.
    page.wait_for_timeout.side_effect = lambda _ms: None
    return sess


# ---------- load_access_token ----------------------------------------------
def test_load_access_token_missing_state_file_returns_none(config: Config) -> None:
    assert not config.browser_state_path.exists()
    assert load_access_token(config) is None


def test_load_access_token_corrupt_state_file_returns_none(config: Config) -> None:
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text("{ this is not json")
    assert load_access_token(config) is None


def test_load_access_token_state_without_token_returns_none(config: Config) -> None:
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(
        '{"cookies": [], "origins": ['
        '{"origin": "https://test.example", "localStorage": ['
        '{"name": "irrelevant", "value": "x"}'
        "]}]}",
    )
    assert load_access_token(config) is None


def test_load_access_token_returns_value_when_present(config: Config) -> None:
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(
        '{"cookies": [], "origins": ['
        '{"origin": "https://test.example", "localStorage": ['
        '{"name": "accessToken", "value": "eyJhbGci.test.jwt"}'
        "]}]}",
    )
    assert load_access_token(config) == "eyJhbGci.test.jwt"


def test_load_access_token_ignores_other_origins(config: Config) -> None:
    """An accessToken for a different origin must not match."""
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(
        '{"cookies": [], "origins": ['
        '{"origin": "https://different.example", "localStorage": ['
        '{"name": "accessToken", "value": "wrong-origin-token"}'
        "]}]}",
    )
    assert load_access_token(config) is None


# ---------- save_tokens ---------------------------------------------------
def test_save_tokens_creates_state_file(config: Config) -> None:
    assert not config.browser_state_path.exists()
    save_tokens(config, access="new-access", refresh="new-refresh", roles="new-roles")
    assert config.browser_state_path.exists()
    state = json.loads(config.browser_state_path.read_text())
    origin = next(o for o in state["origins"] if o["origin"] == config.base_url)
    by_name = {kv["name"]: kv["value"] for kv in origin["localStorage"]}
    assert by_name["accessToken"] == "new-access"
    assert by_name["refreshToken"] == "new-refresh"
    assert by_name["rolesToken"] == "new-roles"


def test_save_tokens_updates_existing_state(config: Config) -> None:
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    initial = {
        "cookies": [{"name": "preserve", "value": "me", "domain": "test.example"}],
        "origins": [
            {
                "origin": config.base_url,
                "localStorage": [
                    {"name": "accessToken", "value": "old-access"},
                    {"name": "refreshToken", "value": "old-refresh"},
                    {"name": "unrelated", "value": "kept"},
                ],
            },
        ],
    }
    config.browser_state_path.write_text(json.dumps(initial))
    save_tokens(config, access="ACCESS-NEW", refresh="REFRESH-NEW")
    state = json.loads(config.browser_state_path.read_text())
    # Cookies preserved
    assert state["cookies"][0]["name"] == "preserve"
    # localStorage values updated, unrelated entries kept
    origin = next(o for o in state["origins"] if o["origin"] == config.base_url)
    by_name = {kv["name"]: kv["value"] for kv in origin["localStorage"]}
    assert by_name["accessToken"] == "ACCESS-NEW"
    assert by_name["refreshToken"] == "REFRESH-NEW"
    assert by_name["unrelated"] == "kept"


def test_save_tokens_recovers_from_corrupt_state(config: Config) -> None:
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text("{ corrupt")
    save_tokens(config, access="A", refresh="R")
    state = json.loads(config.browser_state_path.read_text())
    origin = next(o for o in state["origins"] if o["origin"] == config.base_url)
    by_name = {kv["name"]: kv["value"] for kv in origin["localStorage"]}
    assert by_name == {"accessToken": "A", "refreshToken": "R"}


# ---------- refresh_access_token -----------------------------------------
@responses.activate
def test_refresh_access_token_happy_path() -> None:
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"access": "A2", "refresh": "R2", "roles": "Rol2"},
        status=200,
    )
    result = refresh_access_token("OLD-REFRESH", user_agent="ua/1.0")
    assert result == {"access": "A2", "refresh": "R2", "roles": "Rol2"}
    # Bearer must be the *refresh* token, not access
    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer OLD-REFRESH"
    assert sent.headers["Content-Type"] == "application/json"
    assert sent.headers["User-Agent"] == "ua/1.0"
    assert sent.body in (b"{}", "{}")


@responses.activate
def test_refresh_access_token_401_raises_authentication_error() -> None:
    responses.add(responses.POST, REFRESH_URL, json={"errors": [{}]}, status=401)
    with pytest.raises(AuthenticationError, match="Refresh token rejected"):
        refresh_access_token("DEAD-REFRESH")


@responses.activate
def test_refresh_access_token_other_failure_raises_gamesheet_error() -> None:
    responses.add(responses.POST, REFRESH_URL, status=500, body="boom")
    with pytest.raises(GameSheetError, match="HTTP 500"):
        refresh_access_token("R")


# ---------- AuthenticatedSession -----------------------------------------
# ---------- load_refresh_token (line 348) ------------------------------------
def test_load_refresh_token_returns_value_when_present(config: Config) -> None:
    from gamesheet_sdk.auth import load_refresh_token as _load_refresh_token

    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(
        '{"cookies": [], "origins": ['
        '{"origin": "https://test.example", "localStorage": ['
        '{"name": "refreshToken", "value": "eyJhbGci.refresh.jwt"}'
        "]}]}",
    )
    assert _load_refresh_token(config) == "eyJhbGci.refresh.jwt"


# ---------- _origin_entry_for existing origin match (line 367) --------------
def test_save_tokens_finds_existing_origin(config: Config) -> None:
    """save_tokens should reuse an existing origin entry for the base_url."""
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    initial = {
        "cookies": [],
        "origins": [
            {
                "origin": config.base_url,
                "localStorage": [{"name": "old", "value": "v"}],
            },
        ],
    }
    config.browser_state_path.write_text(json.dumps(initial))
    save_tokens(config, access="A")
    state = json.loads(config.browser_state_path.read_text())
    # Should still be exactly one origin entry
    assert len(state["origins"]) == 1
    assert state["origins"][0]["origin"] == config.base_url


# ---------- _build_token_updates with refresh and roles (lines 382, 384) ----
def test_save_tokens_omits_refresh_when_not_provided(config: Config) -> None:
    """save_tokens with only access token should not write refreshToken."""
    save_tokens(config, access="ACCESS-ONLY")
    state = json.loads(config.browser_state_path.read_text())
    origin = next(o for o in state["origins"] if o["origin"] == config.base_url)
    by_name = {kv["name"]: kv["value"] for kv in origin["localStorage"]}
    assert "accessToken" in by_name
    assert "refreshToken" not in by_name
    assert "rolesToken" not in by_name


def test_save_tokens_includes_roles_when_provided(config: Config) -> None:
    """save_tokens with roles should write rolesToken."""
    save_tokens(config, access="A", roles="ROLES")
    state = json.loads(config.browser_state_path.read_text())
    origin = next(o for o in state["origins"] if o["origin"] == config.base_url)
    by_name = {kv["name"]: kv["value"] for kv in origin["localStorage"]}
    assert by_name["rolesToken"] == "ROLES"


# ---------- firebase error message edge cases (line 157->159) ---------------
# ---------- _origin_entry_for with multiple origins (line 367->366) ---------
def test_save_tokens_with_multiple_origins_finds_correct_one(config: Config) -> None:
    """save_tokens should find the correct origin when multiple exist."""
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    initial = {
        "cookies": [],
        "origins": [
            {
                "origin": "https://other1.example",
                "localStorage": [{"name": "other", "value": "v1"}],
            },
            {
                "origin": "https://other2.example",
                "localStorage": [{"name": "other", "value": "v2"}],
            },
            {
                "origin": config.base_url,
                "localStorage": [{"name": "old", "value": "v3"}],
            },
        ],
    }
    config.browser_state_path.write_text(json.dumps(initial))
    save_tokens(config, access="NEW")
    state = json.loads(config.browser_state_path.read_text())
    # Should still have all three origins
    assert len(state["origins"]) == 3
    # The correct origin should be updated
    target_origin = next(o for o in state["origins"] if o["origin"] == config.base_url)
    by_name = {kv["name"]: kv["value"] for kv in target_origin["localStorage"]}
    assert by_name["accessToken"] == "NEW"
    # Other origins should be unchanged
    other1 = next(o for o in state["origins"] if o["origin"] == "https://other1.example")
    assert other1["localStorage"][0]["value"] == "v1"

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for :mod:`gamesheet_sdk.session`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import responses

from gamesheet_sdk import DEFAULT_BASE_URL, Config, Session
from tests.fixtures.constants import TEST_ERROR_DISK_FULL, TEST_ERROR_PERMISSION_DENIED


def test_default_user_agent_is_version_stamped(config: Config) -> None:
    """Test that default User-Agent header includes version."""
    with Session(config) as sess:
        # Session.headers is typed `str | bytes` (matches the requests stub);
        # the SDK only ever stores a str, so narrow here for static checkers.
        ua = str(sess.headers["User-Agent"])

    assert ua.startswith("gamesheet-sdk-py/")
    assert "github.com/bdperkin/gamesheet-sdk-py" in ua


def test_user_agent_override(config: Config) -> None:
    """Test that custom user_agent config overrides default User-Agent."""
    config.user_agent = "custom-agent/1.0"
    with Session(config) as sess:
        assert sess.headers["User-Agent"] == "custom-agent/1.0"


@responses.activate
def test_relative_url_resolves_against_base(config: Config) -> None:
    """Test that relative URLs are resolved against base_url."""
    responses.add(
        responses.GET,
        "https://test.example/api/leagues",
        json={"leagues": []},
        status=200,
    )
    with Session(config) as sess:
        resp = sess.get("/api/leagues")

    assert resp.status_code == 200
    assert resp.json() == {"leagues": []}


@responses.activate
def test_absolute_url_used_verbatim(config: Config) -> None:
    """Test that absolute URLs bypass base_url resolution."""
    responses.add(
        responses.GET,
        "https://other.example/foo",
        body="ok",
        status=200,
    )
    with Session(config) as sess:
        resp = sess.get("https://other.example/foo")

    assert resp.text == "ok"


@responses.activate
def test_post_put_delete_resolve_too(config: Config) -> None:
    """Test that POST/PUT/DELETE methods also resolve relative URLs."""
    responses.add(responses.POST, "https://test.example/a", status=201)
    responses.add(responses.PUT, "https://test.example/b", status=204)
    responses.add(responses.DELETE, "https://test.example/c", status=204)
    # The requests are issued outside the assertions on purpose: `python -O`
    # strips asserts, which would skip the calls this test exists to make.
    with Session(config) as sess:
        post_response = sess.post("/a")
        put_response = sess.put("/b")
        delete_response = sess.delete("/c")

    assert post_response.status_code == 201
    assert put_response.status_code == 204
    assert delete_response.status_code == 204


@responses.activate
def test_cookies_persist_across_session_lifecycles(config: Config) -> None:
    """Test that cookies are saved and restored across session lifecycles."""
    responses.add(
        responses.GET,
        "https://test.example/login",
        headers={"Set-Cookie": "auth=token123; Path=/; Domain=test.example"},
        status=200,
    )
    with Session(config) as sess:
        sess.get("/login")
        assert sess.cookies.get("auth") == "token123"

    assert config.session_path.exists()
    # A fresh Session against the same config picks the cookie back up.
    with Session(config) as sess2:
        assert sess2.cookies.get("auth") == "token123"


def test_save_creates_parent_dirs(config: Config) -> None:
    """Test that saving session creates parent directories if needed."""
    nested = config.session_path.parent / "deep" / "nest" / "session.json"
    config.session_path = nested
    sess = Session(config)
    sess.cookies.set("foo", "bar", domain="test.example", path="/")
    sess.close()
    assert nested.exists()
    data = json.loads(nested.read_text())
    names = {c["name"]: c["value"] for c in data["cookies"]}
    assert names == {"foo": "bar"}


def test_corrupt_cookie_file_does_not_crash(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A malformed session.json should be ignored with a warning, not raise."""
    config.session_path.parent.mkdir(parents=True, exist_ok=True)
    config.session_path.write_text("{ this is not json")
    with caplog.at_level("WARNING"):
        sess = Session(config)

    assert "Failed to load session cookies" in caplog.text
    assert not sess.cookies
    sess.close()


def test_browser_state_cookies_are_loaded(config: Config) -> None:
    """Browser state cookies should be loaded from browser-state.json."""
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    browser_state_data = {
        "cookies": [
            {
                "name": "browser_cookie",
                "value": "browser_value",
                "domain": ".example.com",
                "path": "/",
                "secure": True,
                "expires": 1234567890,
            },
        ],
    }
    config.browser_state_path.write_text(json.dumps(browser_state_data))
    sess = Session(config)
    assert sess.cookies.get("browser_cookie") == "browser_value"
    sess.close()


def test_corrupt_browser_state_file_does_not_crash(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A malformed browser-state.json should be ignored with a warning, not raise."""
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text("{ this is not json")
    with caplog.at_level("WARNING"):
        sess = Session(config)

    assert "Failed to load browser state cookies" in caplog.text
    assert not sess.cookies
    sess.close()


def test_unreadable_browser_state_file_does_not_crash(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unreadable browser-state.json should be ignored with a warning, not raise."""
    from unittest.mock import patch

    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text('{"cookies": []}')

    # Mock only the specific Path instance's read_text to raise OSError
    original_read_text = Path.read_text

    def selective_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        # Raise OSError only for browser_state_path
        if self == config.browser_state_path:
            raise OSError(TEST_ERROR_PERMISSION_DENIED)
        # For all other paths, use the original method
        return original_read_text(self, *args, **kwargs)

    with (
        patch.object(Path, "read_text", selective_read_text),
        caplog.at_level("WARNING"),
    ):
        sess = Session(config)

    assert "Failed to load browser state cookies" in caplog.text
    assert TEST_ERROR_PERMISSION_DENIED in caplog.text
    sess.close()


def test_missing_cookie_file_is_silent(config: Config) -> None:
    """Test that missing cookie file doesn't raise an error."""
    assert not config.session_path.exists()
    sess = Session(config)
    assert not sess.cookies
    sess.close()


@responses.activate
def test_explicit_timeout_overrides_default(config: Config) -> None:
    """A per-call timeout is forwarded to the underlying request."""
    captured: dict[str, object] = {}

    def callback(*__args: Any, **__kwargs: Any) -> tuple[int, dict[str, str], str]:
        captured["called"] = True
        return (200, {}, "ok")

    responses.add_callback(
        responses.GET,
        "https://test.example/timed",
        callback=callback,
    )
    with Session(config) as sess:
        # Explicit timeout is accepted; we cannot easily assert the value
        # reaches urllib3 without deeper plumbing, but the call must succeed.
        resp = sess.get("/timed", timeout=0.5)

    assert resp.status_code == 200
    assert captured["called"] is True


def test_default_config_when_none_passed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`Session()` with no Config should construct a default Config."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    sess = Session()
    assert sess.config.base_url == DEFAULT_BASE_URL
    sess.close()


def test_set_bearer_token_attaches_authorization_header(config: Config) -> None:
    """Test that set_bearer_token attaches Authorization header."""
    with Session(config) as sess:
        sess.set_bearer_token("eyJhbGci.test.jwt")
        assert sess.headers["Authorization"] == "Bearer eyJhbGci.test.jwt"


def test_set_bearer_token_replaces_existing(config: Config) -> None:
    """Test that set_bearer_token replaces existing Authorization header."""
    with Session(config) as sess:
        sess.set_bearer_token("old")
        sess.set_bearer_token("new")
        assert sess.headers["Authorization"] == "Bearer new"


def test_user_agent_falls_back_when_package_not_found() -> None:
    """Test that user agent falls back to '0+unknown' when package metadata is missing."""
    from unittest.mock import patch

    from gamesheet_sdk.common.session import _default_user_agent

    with patch("gamesheet_sdk.common.session._resolved_version") as mock_version:
        from importlib.metadata import PackageNotFoundError

        mock_version.side_effect = PackageNotFoundError("gamesheet-sdk-py")
        ua = _default_user_agent()

    assert ua == "gamesheet-sdk-py/0+unknown (+https://github.com/bdperkin/gamesheet-sdk-py)"


def test_close_handles_save_oserror_gracefully(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that close() logs warning but continues when save() raises OSError."""
    from unittest.mock import patch

    sess = Session(config)
    sess.cookies.set("test", "value", domain="test.example")
    # Mock the save method to raise OSError
    with (
        patch.object(sess, "save", side_effect=OSError(TEST_ERROR_DISK_FULL)),
        caplog.at_level("WARNING"),
    ):
        sess.close()

    assert "Failed to save session cookies" in caplog.text
    assert TEST_ERROR_DISK_FULL in caplog.text


@responses.activate
def test_patch_resolves_relative_urls(config: Config) -> None:
    """Test that PATCH method resolves relative URLs."""
    responses.add(responses.PATCH, "https://test.example/resource", status=204)
    with Session(config) as sess:
        resp = sess.patch("/resource")

    assert resp.status_code == 204

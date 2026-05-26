"""Tests for :mod:`gamesheet_sdk.session`."""

# pylint: disable=redefined-outer-name  # pytest fixtures are accessed by name

from __future__ import annotations

import json
from pathlib import Path

import pytest
import responses

from gamesheet_sdk import Config, Session


def test_default_user_agent_is_version_stamped(config: Config) -> None:
    with Session(config) as sess:
        ua = sess.headers["User-Agent"]
    assert ua.startswith("gamesheet-sdk-py/")
    assert "github.com/bdperkin/gamesheet-sdk-py" in ua


def test_user_agent_override(config: Config) -> None:
    config.user_agent = "custom-agent/1.0"
    with Session(config) as sess:
        assert sess.headers["User-Agent"] == "custom-agent/1.0"


@responses.activate
def test_relative_url_resolves_against_base(config: Config) -> None:
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
    responses.add(responses.POST, "https://test.example/a", status=201)
    responses.add(responses.PUT, "https://test.example/b", status=204)
    responses.add(responses.DELETE, "https://test.example/c", status=204)
    with Session(config) as sess:
        assert sess.post("/a").status_code == 201
        assert sess.put("/b").status_code == 204
        assert sess.delete("/c").status_code == 204


@responses.activate
def test_cookies_persist_across_session_lifecycles(config: Config) -> None:
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
    nested = config.session_path.parent / "deep" / "nest" / "session.json"
    config.session_path = nested
    sess = Session(config)
    sess.cookies.set("foo", "bar", domain="test.example", path="/")
    sess.close()
    assert nested.exists()
    data = json.loads(nested.read_text())
    names = {c["name"]: c["value"] for c in data["cookies"]}
    assert names == {"foo": "bar"}


def test_corrupt_cookie_file_does_not_crash(config: Config, caplog: pytest.LogCaptureFixture) -> None:
    """A malformed session.json should be ignored with a warning, not raise."""
    config.session_path.parent.mkdir(parents=True, exist_ok=True)
    config.session_path.write_text("{ this is not json")
    with caplog.at_level("WARNING"):
        sess = Session(config)
    assert "Failed to load session cookies" in caplog.text
    assert len(sess.cookies) == 0
    sess.close()


def test_missing_cookie_file_is_silent(config: Config) -> None:
    assert not config.session_path.exists()
    sess = Session(config)
    assert len(sess.cookies) == 0
    sess.close()


@responses.activate
def test_explicit_timeout_overrides_default(config: Config) -> None:
    """A per-call timeout is forwarded to the underlying request."""
    captured: dict[str, object] = {}

    def callback(_req: object) -> tuple[int, dict[str, str], str]:
        captured["called"] = True
        return (200, {}, "ok")

    responses.add_callback(responses.GET, "https://test.example/timed", callback=callback)
    with Session(config) as sess:
        # Explicit timeout is accepted; we cannot easily assert the value
        # reaches urllib3 without deeper plumbing, but the call must succeed.
        resp = sess.get("/timed", timeout=0.5)
    assert resp.status_code == 200
    assert captured["called"] is True


def test_default_config_when_none_passed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`Session()` with no Config should construct a default Config."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    sess = Session()
    assert sess.config.base_url == "https://gamesheet.app"
    sess.close()


def test_set_bearer_token_attaches_authorization_header(config: Config) -> None:
    with Session(config) as sess:
        sess.set_bearer_token("eyJhbGci.test.jwt")
        assert sess.headers["Authorization"] == "Bearer eyJhbGci.test.jwt"


def test_set_bearer_token_replaces_existing(config: Config) -> None:
    with Session(config) as sess:
        sess.set_bearer_token("old")
        sess.set_bearer_token("new")
        assert sess.headers["Authorization"] == "Bearer new"

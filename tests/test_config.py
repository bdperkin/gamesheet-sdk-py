"""Tests for :mod:`gamesheet_sdk.config`."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from gamesheet_sdk import DEFAULT_BASE_URL, Config  # pylint: disable=no-name-in-module

if TYPE_CHECKING:

    from pathlib import Path

    from pydantic import SecretStr


def test_defaults() -> None:

    cfg = Config()
    assert cfg.base_url == DEFAULT_BASE_URL
    assert cfg.username is None
    assert cfg.password is None
    assert cfg.timeout == 30.0
    assert cfg.request_retries == 3
    assert cfg.verify_ssl
    assert cfg.user_agent is None


def test_init_kwargs_override_defaults() -> None:

    cfg = Config(base_url="https://example.test", timeout=5.0, request_retries=0)
    assert cfg.base_url == "https://example.test"
    assert cfg.timeout == 5.0
    assert not cfg.request_retries


def test_env_vars_are_picked_up(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("GAMESHEET_USERNAME", "alice")
    monkeypatch.setenv("GAMESHEET_PASSWORD", "hunter2")
    monkeypatch.setenv("GAMESHEET_TIMEOUT", "10")
    cfg = Config()
    assert cfg.username == "alice"
    assert cfg.password is not None
    # pylint: disable-next=no-member
    assert cfg.password.get_secret_value() == "hunter2"
    assert cfg.timeout == 10.0


def test_init_kwargs_override_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("GAMESHEET_USERNAME", "alice")
    cfg = Config(username="bob")
    assert cfg.username == "bob"


def test_password_is_redacted_in_repr() -> None:

    cfg = Config(password=cast("SecretStr", "hunter2"))
    rendered = repr(cfg)
    assert "hunter2" not in rendered
    assert "SecretStr" in rendered or "**********" in rendered


def test_negative_timeout_rejected() -> None:

    with pytest.raises(ValueError, match=r"Input should be greater than 0"):
        Config(timeout=-1.0)


def test_zero_timeout_rejected() -> None:

    with pytest.raises(ValueError, match=r"Input should be greater than 0"):
        Config(timeout=0.0)


def test_negative_retries_rejected() -> None:

    with pytest.raises(ValueError, match=r"Input should be greater than or equal to 0"):
        Config(request_retries=-1)  # pyrefly: ignore[bad-argument-type]  # intentional invalid value


def test_session_path_default_uses_xdg_cache_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cfg = Config()
    assert cfg.session_path == tmp_path / "gamesheet-sdk-py" / "session.json"


def test_session_path_explicit_override(tmp_path: Path) -> None:

    p = tmp_path / "custom" / "session.json"
    cfg = Config(session_path=p)
    assert cfg.session_path == p


def test_extra_env_vars_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """`GAMESHEET_*` env vars that don't match a field should not raise."""
    monkeypatch.setenv("GAMESHEET_NONEXISTENT_FIELD", "value")
    Config()  # Must not raise.


def test_browser_state_path_default_uses_xdg_cache_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cfg = Config()
    assert cfg.browser_state_path == tmp_path / "gamesheet-sdk-py" / "browser-state.json"


def test_browser_headless_default_true() -> None:

    assert Config().browser_headless


def test_browser_headless_env_var(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("GAMESHEET_BROWSER_HEADLESS", "false")
    assert not Config().browser_headless

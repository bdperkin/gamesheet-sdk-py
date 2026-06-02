"""Tests for :mod:`gamesheet_sdk.browser`.

Most cases exercise the lazy lifecycle without launching a real browser; one lifecycle test mocks Playwright
end-to-end to verify ``_start`` / ``close`` plumbing. A separate ``@pytest.mark.browser`` suite (not in this
file yet) will exercise the real engine once the first browser-driven feature lands.
"""

# pylint: disable=redefined-outer-name,protected-access
# - redefined-outer-name: pytest fixtures share names with the params they bind
# - protected-access: tests legitimately inspect Session/BrowserSession internals

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gamesheet_sdk import BrowserSession, Config

# ---------- construction is lazy / side-effect-free ----------------------


def test_construction_does_not_start_playwright(config: Config) -> None:
    """Just building a BrowserSession should not touch Playwright."""
    with patch("gamesheet_sdk.browser.sync_playwright") as mocked:
        BrowserSession(config)
    mocked.assert_not_called()


def test_save_without_start_is_noop(config: Config) -> None:
    bs = BrowserSession(config)
    bs.save()
    assert not config.browser_state_path.exists()


def test_close_without_start_is_idempotent(config: Config) -> None:
    bs = BrowserSession(config)
    bs.close()
    bs.close()  # second close must not raise


def test_context_after_close_raises(config: Config) -> None:
    bs = BrowserSession(config)
    bs.close()
    with pytest.raises(RuntimeError, match="closed"):
        _ = bs.context


# ---------- URL resolution -----------------------------------------------


def test_resolve_relative(config: Config) -> None:
    bs = BrowserSession(config)
    assert bs._resolve("/login") == "https://test.example/login"


def test_resolve_absolute_passes_through(config: Config) -> None:
    bs = BrowserSession(config)
    assert bs._resolve("https://other.example/x") == "https://other.example/x"


def test_resolve_data_url_passes_through(config: Config) -> None:
    bs = BrowserSession(config)
    assert bs._resolve("data:text/html,<h1>x</h1>") == "data:text/html,<h1>x</h1>"


def test_resolve_about_blank_passes_through(config: Config) -> None:
    bs = BrowserSession(config)
    assert bs._resolve("about:blank") == "about:blank"


# ---------- storage-state load / save ------------------------------------


def test_load_storage_state_missing_returns_none(config: Config) -> None:
    assert not config.browser_state_path.exists()
    bs = BrowserSession(config)
    assert bs._load_storage_state() is None


def test_load_storage_state_reads_json(config: Config) -> None:
    state = {"cookies": [{"name": "x", "value": "y"}], "origins": []}
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(json.dumps(state))
    bs = BrowserSession(config)
    assert bs._load_storage_state() == state


def test_load_storage_state_corrupt_warns_and_returns_none(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text("{ not valid json")
    bs = BrowserSession(config)
    with caplog.at_level("WARNING"):
        result = bs._load_storage_state()
    assert result is None
    assert "Failed to load browser storage state" in caplog.text


def test_save_writes_state_to_disk(config: Config) -> None:
    fake_state: dict[str, Any] = {
        "cookies": [{"name": "a", "value": "b", "domain": "test.example"}],
        "origins": [],
    }
    fake_context = MagicMock()
    fake_context.storage_state.return_value = fake_state

    bs = BrowserSession(config)
    bs._context = fake_context  # inject without launching
    bs.save()

    assert config.browser_state_path.exists()
    assert json.loads(config.browser_state_path.read_text()) == fake_state


def test_save_creates_parent_dirs(config: Config) -> None:
    nested = config.browser_state_path.parent / "deep" / "nest" / "state.json"
    config.browser_state_path = nested
    fake_state: dict[str, Any] = {"cookies": [], "origins": []}
    fake_context = MagicMock()
    fake_context.storage_state.return_value = fake_state

    bs = BrowserSession(config)
    bs._context = fake_context
    bs.save()

    assert nested.exists()


# ---------- full lifecycle, with Playwright mocked end-to-end ------------


def _mock_playwright_chain() -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    """Build a sync_playwright() chain whose intermediate mocks we can assert on."""
    pw_factory = MagicMock(name="sync_playwright_factory")
    pw_runtime = MagicMock(name="playwright_runtime")
    browser = MagicMock(name="browser")
    context = MagicMock(name="context")

    pw_factory.return_value.start.return_value = pw_runtime
    pw_runtime.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    # close() calls save() which calls storage_state(); give it a valid
    # JSON-serializable default so tests that don't override don't crash.
    context.storage_state.return_value = {"cookies": [], "origins": []}

    return pw_factory, pw_runtime, browser, context


def test_start_launches_chromium_headless_by_default(config: Config) -> None:
    pw_factory, pw_runtime, browser, context = _mock_playwright_chain()
    with patch("gamesheet_sdk.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context  # triggers _start
    pw_factory.assert_called_once_with()
    pw_runtime.chromium.launch.assert_called_once_with(headless=True)
    browser.new_context.assert_called_once_with()
    assert bs._context is context


def test_start_passes_headless_false_when_configured(config: Config) -> None:
    config.browser_headless = False
    pw_factory, pw_runtime, _, _ = _mock_playwright_chain()
    with patch("gamesheet_sdk.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context
    pw_runtime.chromium.launch.assert_called_once_with(headless=False)
    bs.close()  # exercise close on a mocked chain too


def test_start_restores_storage_state_when_file_exists(config: Config) -> None:
    state = {"cookies": [{"name": "auth", "value": "tok"}], "origins": []}
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(json.dumps(state))

    pw_factory, _, browser, _ = _mock_playwright_chain()
    with patch("gamesheet_sdk.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context
    browser.new_context.assert_called_once_with(storage_state=state)
    bs.close()


def test_close_tears_down_in_order(config: Config) -> None:
    pw_factory, pw_runtime, browser, context = _mock_playwright_chain()
    with patch("gamesheet_sdk.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context  # trigger _start
        bs.close()

    context.close.assert_called_once_with()
    browser.close.assert_called_once_with()
    pw_runtime.stop.assert_called_once_with()
    assert bs._context is None
    assert bs._closed


def test_context_manager_saves_on_exit(config: Config) -> None:
    fake_state = {"cookies": [{"name": "k", "value": "v"}], "origins": []}
    pw_factory, _, _, context = _mock_playwright_chain()
    context.storage_state.return_value = fake_state

    with patch("gamesheet_sdk.browser.sync_playwright", pw_factory), BrowserSession(config) as bs:
        _ = bs.context  # force start

    assert config.browser_state_path.exists()
    assert json.loads(config.browser_state_path.read_text()) == fake_state


def test_goto_resolves_url_and_returns_page(config: Config) -> None:
    pw_factory, _, _, context = _mock_playwright_chain()
    page = MagicMock(name="page")
    context.new_page.return_value = page

    with patch("gamesheet_sdk.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        returned = bs.goto("/login", wait_until="domcontentloaded")
        bs.close()

    page.goto.assert_called_once_with("https://test.example/login", wait_until="domcontentloaded")
    assert returned is page

# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for :mod:`gamesheet_sdk.browser`.

Most cases exercise the lazy lifecycle without launching a real browser; one lifecycle test mocks Playwright
end-to-end to verify ``_start`` / ``close`` plumbing. A separate ``@pytest.mark.browser`` suite (not in this
file yet) will exercise the real engine once the first browser-driven feature lands.
"""

# - redefined-outer-name: pytest fixtures share names with the params they bind
# - protected-access: tests legitimately inspect Session/BrowserSession internals
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gamesheet_sdk import BrowserSession, Config
from tests.fixtures.constants import TEST_ERROR_DISK_FULL


# ---------- construction is lazy / side-effect-free ----------------------
def test_construction_does_not_start_playwright(config: Config) -> None:
    """Just building a BrowserSession should not touch Playwright."""
    with patch("gamesheet_sdk.common.browser.sync_playwright") as mocked:
        BrowserSession(config)

    mocked.assert_not_called()


def test_save_without_start_is_noop(config: Config) -> None:
    """Test that save() without start() doesn't create state file."""
    bs = BrowserSession(config)
    bs.save()
    assert not config.browser_state_path.exists()


def test_close_without_start_is_idempotent(config: Config) -> None:
    """Test that close() can be called multiple times safely without start()."""
    bs = BrowserSession(config)
    bs.close()
    bs.close()  # second close must not raise


def test_context_after_close_raises(config: Config) -> None:
    """Test that accessing context property after close raises RuntimeError."""
    bs = BrowserSession(config)
    bs.close()
    with pytest.raises(RuntimeError, match="closed"):
        _ = bs.context


# ---------- URL resolution -----------------------------------------------
def test_resolve_relative(config: Config) -> None:
    """Test that relative URLs are resolved against base_url."""
    bs = BrowserSession(config)
    assert bs._resolve("/login") == "https://test.example/login"


def test_resolve_absolute_passes_through(config: Config) -> None:
    """Test that absolute URLs bypass base_url resolution."""
    bs = BrowserSession(config)
    assert bs._resolve("https://other.example/x") == "https://other.example/x"


def test_resolve_data_url_passes_through(config: Config) -> None:
    """Test that data: URLs are passed through unchanged."""
    bs = BrowserSession(config)
    assert bs._resolve("data:text/html,<h1>x</h1>") == "data:text/html,<h1>x</h1>"


def test_resolve_about_blank_passes_through(config: Config) -> None:
    """Test that about:blank URLs are passed through unchanged."""
    bs = BrowserSession(config)
    assert bs._resolve("about:blank") == "about:blank"


# ---------- storage-state load / save ------------------------------------
def test_load_storage_state_missing_returns_none(config: Config) -> None:
    """Test that loading storage state from missing file returns None."""
    assert not config.browser_state_path.exists()
    bs = BrowserSession(config)
    assert bs._load_storage_state() is None


def test_load_storage_state_reads_json(config: Config) -> None:
    """Test that loading storage state successfully reads JSON from file."""
    state = {"cookies": [{"name": "x", "value": "y"}], "origins": []}
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(json.dumps(state))
    bs = BrowserSession(config)
    assert bs._load_storage_state() == state


def test_load_storage_state_corrupt_warns_and_returns_none(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that corrupt storage state file logs warning and returns None."""
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text("{ not valid json")
    bs = BrowserSession(config)
    with caplog.at_level("WARNING"):
        result = bs._load_storage_state()

    assert result is None
    assert "Failed to load browser storage state" in caplog.text


def test_save_writes_state_to_disk(config: Config) -> None:
    """Test that save() writes browser storage state to disk."""
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
    """Test that save() creates parent directories if needed."""
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
    """Test that accessing context launches Chromium in headless mode by default."""
    pw_factory, pw_runtime, browser, context = _mock_playwright_chain()
    with patch("gamesheet_sdk.common.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context  # triggers _start

    pw_factory.assert_called_once_with()
    pw_runtime.chromium.launch.assert_called_once_with(headless=True)
    browser.new_context.assert_called_once_with()
    assert bs._context is context


def test_start_passes_headless_false_when_configured(config: Config) -> None:
    """Test that browser_headless=False launches Chromium in headed mode."""
    config.browser_headless = False
    pw_factory, pw_runtime, _, _ = _mock_playwright_chain()
    with patch("gamesheet_sdk.common.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context

    pw_runtime.chromium.launch.assert_called_once_with(headless=False)
    bs.close()  # exercise close on a mocked chain too


def test_start_restores_storage_state_when_file_exists(config: Config) -> None:
    """Test that starting browser restores storage state from file if it exists."""
    state = {"cookies": [{"name": "auth", "value": "tok"}], "origins": []}
    config.browser_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.browser_state_path.write_text(json.dumps(state))
    pw_factory, _, browser, _ = _mock_playwright_chain()
    with patch("gamesheet_sdk.common.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context

    browser.new_context.assert_called_once_with(storage_state=state)
    bs.close()


def test_close_tears_down_in_order(config: Config) -> None:
    """Test that close() tears down browser context, browser, and Playwright in order."""
    pw_factory, pw_runtime, browser, context = _mock_playwright_chain()
    with patch("gamesheet_sdk.common.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        _ = bs.context  # trigger _start
        bs.close()

    context.close.assert_called_once_with()
    browser.close.assert_called_once_with()
    pw_runtime.stop.assert_called_once_with()
    assert bs._context is None
    assert bs._closed


def test_context_manager_saves_on_exit(config: Config) -> None:
    """Test that using BrowserSession as context manager saves state on exit."""
    fake_state = {"cookies": [{"name": "k", "value": "v"}], "origins": []}
    pw_factory, _, _, context = _mock_playwright_chain()
    context.storage_state.return_value = fake_state
    with (
        patch("gamesheet_sdk.common.browser.sync_playwright", pw_factory),
        BrowserSession(config) as bs,
    ):
        _ = bs.context  # force start

    assert config.browser_state_path.exists()
    assert json.loads(config.browser_state_path.read_text()) == fake_state


def test_goto_resolves_url_and_returns_page(config: Config) -> None:
    """Test that goto() resolves URL and returns page object."""
    pw_factory, _, _, context = _mock_playwright_chain()
    page = MagicMock(name="page")
    context.new_page.return_value = page
    with patch("gamesheet_sdk.common.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        returned = bs.goto("/login", wait_until="domcontentloaded")
        bs.close()

    page.goto.assert_called_once_with(
        "https://test.example/login",
        wait_until="domcontentloaded",
    )
    assert returned is page


# ---------- _start failure path (lines 105-106) -----------------------------
def test_context_raises_when_start_leaves_context_none(config: Config) -> None:
    """Accessing context when _start somehow completes without setting _context should raise ValueError.

    This is a defensive check for an edge case that shouldn't happen in normal operation - _start() will
    either succeed (setting _context) or raise an exception. This test directly manipulates internal state to
    exercise the safety check.
    """
    bs = BrowserSession(config)
    # Bypass _start() entirely and directly access the property with _context=None
    # This simulates the pathological case where _start completed without
    # setting _context or raising (which shouldn't happen in practice).
    with patch.object(bs, "_start") as mock_start:
        # _start is called but leaves _context as None
        mock_start.return_value = None
        bs._context = None  # explicitly keep it None
        with pytest.raises(ValueError, match="did not start"):
            _ = bs.context


def test_close_handles_save_oserror_gracefully(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that close() logs warning but continues when save() raises OSError."""
    fake_context = MagicMock()
    fake_context.storage_state.side_effect = OSError(TEST_ERROR_DISK_FULL)
    bs = BrowserSession(config)
    bs._context = fake_context
    with caplog.at_level("WARNING"):
        bs.close()

    assert "Failed to save browser storage state" in caplog.text
    assert TEST_ERROR_DISK_FULL in caplog.text
    assert bs._closed


def test_context_returns_same_context_on_subsequent_calls(config: Config) -> None:
    """Test that accessing context property multiple times returns the same context without re-starting."""
    pw_factory, _, _, context = _mock_playwright_chain()
    with patch("gamesheet_sdk.common.browser.sync_playwright", pw_factory):
        bs = BrowserSession(config)
        ctx1 = bs.context  # first access triggers _start
        ctx2 = bs.context  # second access should return existing context
        bs.close()

    assert ctx1 is ctx2
    assert ctx1 is context
    # _start should only be called once (on first access)
    pw_factory.assert_called_once_with()

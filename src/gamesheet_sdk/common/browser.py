# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Reusable Playwright browser session for the JS-heavy WebUI path.

Sibling of :mod:`gamesheet_sdk.common.session` with matching shape:
- One context owning cookies and localStorage.
- Storage state persisted via :attr:`Config.browser_state_path`.
- Base-URL resolution against :attr:`Config.base_url`.
- Context-manager that saves state on exit.
Browsers are heavyweight, so :class:`BrowserSession` starts Playwright lazily on first reach for the browser;
bare construction is free.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Self
from urllib.parse import urljoin

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    StorageState,
    sync_playwright,
)

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.security import write_secure_text

if TYPE_CHECKING:
    from types import TracebackType

_LOGGER = logging.getLogger(__name__)


class BrowserSession:
    """A Playwright-driven session for the JavaScript-heavy code path.

    Mirror of :class:`gamesheet_sdk.Session` for flows where ``requests`` is not enough (single-page apps,
    anti-bot challenges, anything that needs a real engine to render).

    Example::

        from gamesheet_sdk import BrowserSession, Config

        with BrowserSession(Config()) as bs:
            page = bs.goto("/login")
            page.fill("input[name='email']", "...")

    Stores the configuration and sets up internal state for lazy browser initialization. Playwright and
    Chromium are only launched when :attr:`context` or :meth:`goto` is first accessed. This makes construction
    cheap and allows sessions that never reach for the browser (e.g. configuration-only runs) to avoid the
    startup overhead.

    Args:
        config (Config | None): Optional configuration object. If ``None``, a default
            :class:`~gamesheet_sdk.common.config.Config` is created.

    """

    def __init__(self: BrowserSession, config: Config | None = None) -> None:
        """Initialize BrowserSession instance.

        Args:
            config (Config | None): Optional SDK configuration object.

        """
        self.config = config or Config()
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._closed = False

    def _load_storage_state(self: BrowserSession) -> StorageState | None:
        """Load browser storage state from disk if it exists.

        Returns:
            StorageState | None: A dictionary containing cookies and localStorage data, or ``None`` if the
                file does not exist or cannot be parsed.

        """
        path = self.config.browser_state_path
        if not path.exists():
            return None

        try:
            loaded: StorageState = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning(
                "Failed to load browser storage state from %s: %s",
                path,
                exc,
            )
            return None

        return loaded

    # -- internals --------------------------------------------------------
    def _start(self: BrowserSession) -> None:
        """Launch Playwright + Chromium + a context, possibly restoring state."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.config.browser_headless,
        )
        storage_state = self._load_storage_state()
        if storage_state is not None:
            # storage_state is read back from the JSON Playwright itself
            # wrote; matches the StorageState TypedDict structurally.
            self._context = self._browser.new_context(
                storage_state=storage_state,
            )
        else:
            self._context = self._browser.new_context()

    # -- public attribute access ------------------------------------------
    @property
    def context(self: BrowserSession) -> BrowserContext:
        """The underlying Playwright BrowserContext.

        Starts Playwright and launches Chromium on first access, so a :class:`BrowserSession` that never
        reaches for the browser is effectively free.

        Returns:
            BrowserContext: The active browser context.

        Raises:
            RuntimeError: If the session has already been closed.
            ValueError: If the browser failed to start (defensive check).

        """
        if self._closed:
            err_msg = "BrowserSession has been closed"
            raise RuntimeError(err_msg)

        if self._context is None:
            self._start()

        if self._context is None:
            # Defensive check: _start() either succeeds (sets _context) or raises
            err_msg = "BrowserSession did not start"
            raise ValueError(err_msg)

        return self._context

    def new_page(self: BrowserSession) -> Page:
        """Open a fresh tab in the session's context and return it.

        Starts Playwright and Chromium on first call if not already running.

        Returns:
            Page: Return value.

        """
        return self.context.new_page()

    def _resolve(self: BrowserSession, url: str) -> str:
        """Resolve a URL against the configured base URL.

        Absolute URLs (http://, https://, data:, file:, about:) are returned unchanged. Relative URLs are
        joined to :attr:`Config.base_url`.

        Args:
            url (str): An absolute or relative URL.

        Returns:
            str: String result.

        """
        if url.startswith(("http://", "https://", "data:", "file:", "about:")):
            return url

        return urljoin(self.config.base_url.rstrip("/") + "/", url.lstrip("/"))

    def goto(self: BrowserSession, url: str, **kwargs: Any) -> Page:
        """Open a fresh tab navigated to ``url``.

        ``url`` may be absolute or a path relative to :attr:`Config.base_url`. Starts Playwright and Chromium
        on first call if not already running.

        Example::

            with BrowserSession() as bs:
                page = bs.goto("/login", wait_until="networkidle")
                page.fill("input[name='email']", "test@example.com")

        Args:
            url (str): An absolute or relative URL to navigate to.
            **kwargs (Any): Additional keyword arguments passed to :meth:`playwright.sync_api.Page.goto`.

        Returns:
            Page: A :class:`~playwright.sync_api.Page` navigated to the resolved URL.

        """
        page = self.new_page()
        page.goto(self._resolve(url), **kwargs)
        return page

    # -- lifecycle --------------------------------------------------------
    def save(self: BrowserSession) -> None:
        """Persist the current storage state to :attr:`Config.browser_state_path`.

        No-op if the browser has not been started yet (there is nothing to save) or if :meth:`close` has
        already been called.
        """
        if self._context is None:
            return

        path = self.config.browser_state_path
        state = self._context.storage_state()
        write_secure_text(path, json.dumps(state, indent=2, sort_keys=True))

    def _safe_save(self: BrowserSession) -> None:
        """Persist storage state, demoting disk errors to a warning.

        Calls :meth:`save` and logs any :exc:`OSError` as a warning instead of propagating it, ensuring
        cleanup can proceed even if state persistence fails.
        """
        try:
            self.save()
        except OSError as exc:
            _LOGGER.warning("Failed to save browser storage state: %s", exc)

    def _release_playwright(self: BrowserSession) -> None:
        """Close the context/browser/playwright handles and drop our refs.

        Closes the browser context, browser instance, and stops the Playwright driver in that order. Resets
        all internal references to ``None``. Safe to call when some or all handles are already ``None``.

        """
        if self._context is not None:
            self._context.close()

        if self._browser is not None:
            self._browser.close()

        if self._playwright is not None:
            self._playwright.stop()

        self._context = None
        self._browser = None
        self._playwright = None

    def close(self: BrowserSession) -> None:
        """Persist storage state and shut Playwright down.

        Idempotent: calling :meth:`close` more than once is safe.
        """
        if self._closed:
            return

        self._safe_save()
        self._release_playwright()
        self._closed = True

    def __enter__(self: Self) -> Self:
        """Enter the context manager.

        Returns:
            Self: Return value.

        """
        return self

    def __exit__(
        self: BrowserSession,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context manager and close the session.

        Persists storage state and shuts down Playwright resources.

        """
        self.close()

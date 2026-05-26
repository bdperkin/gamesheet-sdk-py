"""Reusable Playwright browser session for the JS-heavy WebUI path.

Sibling of :mod:`gamesheet_sdk.session` with matching shape:

- One context owning cookies and localStorage.
- Storage state persisted via :attr:`Config.browser_state_path`.
- Base-URL resolution against :attr:`Config.base_url`.
- Context-manager that saves state on exit.

Browsers are heavyweight, so :class:`BrowserSession` starts Playwright
lazily on first reach for the browser; bare construction is free.
"""

from __future__ import annotations

import json
import logging
from types import TracebackType
from typing import Any
from urllib.parse import urljoin

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from gamesheet_sdk.config import Config

_LOGGER = logging.getLogger(__name__)


class BrowserSession:
    """A Playwright-driven session for the JavaScript-heavy code path.

    Mirror of :class:`gamesheet_sdk.Session` for flows where ``requests``
    is not enough (single-page apps, anti-bot challenges, anything that
    needs a real engine to render).

    Example::

        from gamesheet_sdk import BrowserSession, Config

        with BrowserSession(Config()) as bs:
            page = bs.goto("/login")
            page.fill("input[name='email']", "...")
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._closed = False

    # -- public attribute access ------------------------------------------

    @property
    def context(self) -> BrowserContext:
        """The underlying Playwright BrowserContext.

        Starts Playwright and launches Chromium on first access, so a
        :class:`BrowserSession` that never reaches for the browser is
        effectively free.
        """
        if self._closed:
            raise RuntimeError("BrowserSession has been closed")
        if self._context is None:
            self._start()
        assert self._context is not None  # nosec B101 - mypy narrowing
        return self._context

    def new_page(self) -> Page:
        """Open a fresh tab in the session's context and return it."""
        return self.context.new_page()

    def goto(self, url: str, **kwargs: Any) -> Page:
        """Open a fresh tab navigated to ``url``.

        ``url`` may be absolute or a path relative to
        :attr:`Config.base_url`. Extra ``kwargs`` are forwarded to
        :meth:`playwright.sync_api.Page.goto`.
        """
        page = self.new_page()
        page.goto(self._resolve(url), **kwargs)
        return page

    # -- lifecycle --------------------------------------------------------

    def save(self) -> None:
        """Persist the current storage state to :attr:`Config.browser_state_path`.

        No-op if the browser has not been started yet (there is nothing
        to save) or if :meth:`close` has already been called.
        """
        if self._context is None:
            return
        path = self.config.browser_state_path
        path.parent.mkdir(parents=True, exist_ok=True)
        state = self._context.storage_state()
        path.write_text(json.dumps(state, indent=2, sort_keys=True))

    def close(self) -> None:
        """Persist storage state and shut Playwright down.

        Idempotent: calling :meth:`close` more than once is safe.
        """
        if self._closed:
            return
        try:
            self.save()
        except OSError as exc:  # pragma: no cover - rare disk failure path
            _LOGGER.warning("Failed to save browser storage state: %s", exc)
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._context = None
        self._browser = None
        self._playwright = None
        self._closed = True

    def __enter__(self) -> BrowserSession:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    # -- internals --------------------------------------------------------

    def _start(self) -> None:
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
                storage_state=storage_state,  # type: ignore[arg-type]
            )
        else:
            self._context = self._browser.new_context()

    def _load_storage_state(self) -> dict[str, Any] | None:
        path = self.config.browser_state_path
        if not path.exists():
            return None
        try:
            loaded: dict[str, Any] = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Failed to load browser storage state from %s: %s", path, exc)
            return None
        return loaded

    def _resolve(self, url: str) -> str:
        if url.startswith(("http://", "https://", "data:", "file:", "about:")):
            return url
        return urljoin(self.config.base_url.rstrip("/") + "/", url.lstrip("/"))

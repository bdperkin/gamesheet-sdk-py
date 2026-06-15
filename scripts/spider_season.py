#!/usr/bin/env python3
"""Spider all GET-traversable paths and mutations for a GameSheet season.

This utility discovers all GET-traversable paths under a season URL, records
all Fetch/XHR network requests, and discovers mutation operations (POST/PATCH/DELETE)
without executing them. The spider uses randomized human-like delays and respects
the base season URL constraint to avoid traversing external links.

Key behaviors:
- Only follows GET requests (safe, read-only operations)
- Records all Fetch/XHR network requests
- Discovers mutation operations (POST/PATCH/DELETE) without executing them
- Randomized delays (2.5-5s) between requests to appear human
- Logs external links without traversing them
- Saves comprehensive mapping data to JSON
- Leverages existing auth infrastructure for login
- Supports custom browser executable path (e.g., /usr/bin/chromium-browser)

Safety guarantees:
- NO data is deleted, modified, updated, or created
- Only GET requests are executed
- POST/PATCH/DELETE operations are discovered but never invoked
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from playwright.sync_api import Page, Request, Response, TimeoutError as PlaywrightTimeoutError

from gamesheet_sdk.auth.login import login
from gamesheet_sdk.browser import BrowserSession
from gamesheet_sdk.config import Config

_LOGGER = logging.getLogger(__name__)

# Human-like delay bounds (seconds)
MIN_DELAY = 2.5
MAX_DELAY = 5.0

# Network request type categories
HTTP_METHODS_SAFE = {"GET", "HEAD", "OPTIONS"}
HTTP_METHODS_MUTATION = {"POST", "PATCH", "PUT", "DELETE"}

# Timeout for page navigation and network settle (ms)
NAV_TIMEOUT_MS = 30_000
NETWORK_SETTLE_MS = 3_000


@dataclass
class DiscoveredMutation:
    """A mutation operation discovered but not executed."""

    method: str
    url: str
    element_type: str | None = None
    element_text: str | None = None
    form_action: str | None = None
    discovered_from_url: str | None = None


@dataclass
class NetworkCapture:
    """A network request captured during traversal."""

    url: str
    method: str
    resource_type: str
    status: int | None = None
    source_page: str | None = None


@dataclass
class SpiderState:
    """Current state of the spider crawl."""

    season_id: str
    base_url: str
    visited_urls: set[str] = field(default_factory=set)
    pending_queue: deque[str] = field(default_factory=deque)
    discovered_mutations: list[DiscoveredMutation] = field(default_factory=list)
    network_captures: list[NetworkCapture] = field(default_factory=list)
    external_links: set[str] = field(default_factory=set)
    error_urls: dict[str, str] = field(default_factory=dict)


class SeasonSpider:
    """Spider for discovering all paths and mutations under a GameSheet season."""

    def __init__(
        self,
        season_id: str,
        config: Config,
        browser_executable: str | None = None,
    ) -> None:
        """Initialize the spider.

        :param season_id: The season ID to spider (e.g., "15020")
        :param config: Configuration object with auth credentials
        :param browser_executable: Optional path to browser executable
        """
        self.season_id = season_id
        self.config = config
        self.browser_executable = browser_executable
        self.state = SpiderState(
            season_id=season_id,
            base_url=f"{config.base_url.rstrip('/')}/seasons/{season_id}",
        )
        self.session: BrowserSession | None = None
        self.page: Page | None = None

    def _is_internal_url(self, url: str) -> bool:
        """Check if a URL is internal to the base season path.

        :param url: URL to check
        :returns: True if URL is under the base season path
        """
        return url.startswith(self.state.base_url)

    def _normalize_url(self, url: str, current_url: str | None = None) -> str:
        """Normalize a URL to an absolute form.

        :param url: URL to normalize (may be relative)
        :param current_url: Current page URL for resolving relative links
        :returns: Normalized absolute URL
        """
        # Remove fragment identifiers
        url = url.split("#")[0]

        # If already absolute, return as-is
        if url.startswith(("http://", "https://")):
            return url

        # Resolve relative URLs against current page or base URL
        base = current_url if current_url else self.state.base_url
        return urljoin(base, url)

    def _setup_network_capture(self, page: Page, source_url: str) -> None:
        """Attach network request/response listeners to a page.

        :param page: Playwright page to attach listeners to
        :param source_url: The source page URL for attribution
        """

        def on_request(request: Request) -> None:
            """Capture outgoing requests."""
            resource_type = request.resource_type
            # Only capture Fetch/XHR and document requests
            if resource_type not in {"fetch", "xhr", "document"}:
                return

            capture = NetworkCapture(
                url=request.url,
                method=request.method,
                resource_type=resource_type,
                source_page=source_url,
            )
            self.state.network_captures.append(capture)
            _LOGGER.debug("Captured %s %s (%s)", request.method, request.url, resource_type)

        def on_response(response: Response) -> None:
            """Capture response status for our tracked requests."""
            # Update the most recent matching capture with status
            for capture in reversed(self.state.network_captures):
                if capture.url == response.url and capture.status is None:
                    capture.status = response.status
                    break

        page.on("request", on_request)
        page.on("response", on_response)

    def _discover_mutations(self, page: Page, current_url: str) -> None:
        """Discover mutation operations without executing them.

        :param page: Playwright page to inspect
        :param current_url: Current page URL for attribution
        """
        # Discover forms with POST/PATCH/DELETE methods
        forms = page.query_selector_all("form")
        for form in forms:
            method_attr = form.get_attribute("method")
            action_attr = form.get_attribute("action")

            if not method_attr:
                method_attr = "GET"  # Forms default to GET

            method = method_attr.upper()
            if method not in HTTP_METHODS_MUTATION:
                continue

            action_url = self._normalize_url(action_attr or current_url, current_url)

            mutation = DiscoveredMutation(
                method=method,
                url=action_url,
                element_type="form",
                form_action=action_attr,
                discovered_from_url=current_url,
            )
            self.state.discovered_mutations.append(mutation)
            _LOGGER.info("Discovered %s form → %s", method, action_url)

        # Discover buttons/links with mutation intent (heuristic)
        # Look for data-method, data-action, or common mutation class names
        mutation_selectors = [
            "button[data-method]",
            "a[data-method]",
            "[data-action*='delete']",
            "[data-action*='remove']",
            "[data-action*='create']",
            "[data-action*='update']",
            "button[type='submit']",
            ".btn-delete",
            ".btn-remove",
            ".delete-btn",
            ".remove-btn",
        ]

        for selector in mutation_selectors:
            try:
                elements = page.query_selector_all(selector)
            except Exception as exc:  # noqa: BLE001
                _LOGGER.debug("Selector '%s' failed: %s", selector, exc)
                continue

            for element in elements:
                # Extract mutation intent
                data_method = element.get_attribute("data-method")
                data_action = element.get_attribute("data-action")
                href = element.get_attribute("href")
                element_text = element.text_content() or ""

                # Determine method
                method = "POST"  # Default assumption
                if data_method:
                    method = data_method.upper()
                elif data_action and "delete" in data_action.lower():
                    method = "DELETE"

                # Determine URL
                target_url = href or current_url
                target_url = self._normalize_url(target_url, current_url)

                mutation = DiscoveredMutation(
                    method=method,
                    url=target_url,
                    element_type=element.evaluate("el => el.tagName.toLowerCase()"),
                    element_text=element_text.strip()[:100],  # Truncate long text
                    discovered_from_url=current_url,
                )
                self.state.discovered_mutations.append(mutation)
                _LOGGER.info(
                    "Discovered %s button/link → %s (%s)",
                    method,
                    target_url,
                    element_text.strip()[:50],
                )

    def _extract_links(self, page: Page, current_url: str) -> list[str]:
        """Extract all clickable links from the current page.

        :param page: Playwright page to extract links from
        :param current_url: Current page URL for resolving relative links
        :returns: List of absolute URLs
        """
        links = []
        link_elements = page.query_selector_all("a[href]")

        for element in link_elements:
            href = element.get_attribute("href")
            if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                continue

            absolute_url = self._normalize_url(href, current_url)
            links.append(absolute_url)

        return links

    def _find_next_unvisited_link(self, page: Page, current_url: str) -> str | None:
        """Find the first unvisited internal link on the current page.

        :param page: Playwright page to search
        :param current_url: Current page URL
        :returns: Next unvisited internal link, or None
        """
        all_links = self._extract_links(page, current_url)

        for link in all_links:
            if link in self.state.visited_urls:
                continue

            if self._is_internal_url(link):
                return link

            # Log external link
            if link not in self.state.external_links:
                self.state.external_links.add(link)
                _LOGGER.info("External link (not traversing): %s", link)

        return None

    def _human_delay(self) -> None:
        """Sleep for a randomized human-like delay."""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        _LOGGER.debug("Human delay: %.2fs", delay)
        time.sleep(delay)

    def _visit_url(self, url: str) -> bool:
        """Visit a URL and perform discovery.

        :param url: URL to visit
        :returns: True if visit succeeded, False on error
        """
        if not self.page:
            _LOGGER.error("Page not initialized")
            return False

        _LOGGER.info("Visiting: %s", url)

        try:
            # Attach network capture before navigation
            self._setup_network_capture(self.page, url)

            # Navigate to URL
            self.page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)

            # Wait for network to settle
            try:
                self.page.wait_for_load_state("networkidle", timeout=NETWORK_SETTLE_MS)
            except PlaywrightTimeoutError:
                _LOGGER.debug("Network didn't settle in %dms, proceeding anyway", NETWORK_SETTLE_MS)

            # Mark as visited
            self.state.visited_urls.add(url)

            # Discover mutations
            self._discover_mutations(self.page, url)

            # Queue unvisited internal links
            next_link = self._find_next_unvisited_link(self.page, url)
            if next_link:
                if next_link not in self.state.pending_queue:
                    self.state.pending_queue.append(next_link)
                    _LOGGER.debug("Queued for visit: %s", next_link)

            return True

        except PlaywrightTimeoutError as exc:
            _LOGGER.warning("Timeout visiting %s: %s", url, exc)
            self.state.error_urls[url] = f"Timeout: {exc}"
            return False

        except Exception as exc:  # noqa: BLE001
            _LOGGER.exception("Error visiting %s: %s", url, exc)
            self.state.error_urls[url] = f"Error: {exc}"
            return False

    def _crawl_loop(self) -> None:
        """Main crawl loop that processes the queue until empty."""
        if not self.page:
            _LOGGER.error("Page not initialized")
            return

        # Start with the base season URL
        self.state.pending_queue.append(self.state.base_url)

        while self.state.pending_queue:
            url = self.state.pending_queue.popleft()

            # Skip if already visited
            if url in self.state.visited_urls:
                continue

            # Skip if not internal
            if not self._is_internal_url(url):
                if url not in self.state.external_links:
                    self.state.external_links.add(url)
                    _LOGGER.info("Skipping external URL: %s", url)
                continue

            # Visit the URL
            self._visit_url(url)

            # Human-like delay before next request
            if self.state.pending_queue:
                self._human_delay()

        _LOGGER.info("Crawl complete. No more unvisited internal URLs.")

    def _create_custom_browser_session(self) -> BrowserSession:
        """Create a BrowserSession with custom browser executable.

        :returns: BrowserSession configured with custom executable
        """
        from playwright.sync_api import sync_playwright

        # Create a custom session that patches the browser launch
        session = BrowserSession(self.config)

        # Override the _start method to use custom executable
        def custom_start() -> None:
            """Launch Playwright with custom executable."""
            session._playwright = sync_playwright().start()
            session._browser = session._playwright.chromium.launch(
                headless=self.config.browser_headless,
                executable_path=self.browser_executable,
            )
            storage_state = session._load_storage_state()
            if storage_state is not None:
                session._context = session._browser.new_context(storage_state=storage_state)
            else:
                session._context = session._browser.new_context()

        session._start = custom_start
        return session

    def _save_results(self, output_path: Path) -> None:
        """Save spider results to a JSON file.

        :param output_path: Path to output JSON file
        """
        results = {
            "season_id": self.state.season_id,
            "base_url": self.state.base_url,
            "crawl_timestamp": time.time(),
            "summary": {
                "visited_urls": len(self.state.visited_urls),
                "discovered_mutations": len(self.state.discovered_mutations),
                "network_captures": len(self.state.network_captures),
                "external_links": len(self.state.external_links),
                "errors": len(self.state.error_urls),
            },
            "visited_urls": sorted(self.state.visited_urls),
            "discovered_mutations": [asdict(m) for m in self.state.discovered_mutations],
            "network_captures": [asdict(n) for n in self.state.network_captures],
            "external_links": sorted(self.state.external_links),
            "error_urls": self.state.error_urls,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2, sort_keys=True))
        _LOGGER.info("Results saved to %s", output_path)

    def run(self, output_path: Path | None = None) -> dict[str, Any]:
        """Execute the spider crawl.

        :param output_path: Optional path to save results JSON
        :returns: Dictionary of crawl results
        """
        _LOGGER.info("Starting spider for season %s", self.season_id)
        _LOGGER.info("Base URL: %s", self.state.base_url)

        # Initialize browser session with custom executable if provided
        if self.browser_executable:
            _LOGGER.info("Using browser executable: %s", self.browser_executable)
            # Create a custom BrowserSession that uses the specified executable
            self.session = self._create_custom_browser_session()
        else:
            self.session = BrowserSession(self.config)

        try:
            # Perform login
            _LOGGER.info("Authenticating...")
            login(self.session)
            _LOGGER.info("Authentication successful")

            # Create a fresh page for crawling
            self.page = self.session.new_page()

            # Execute crawl
            self._crawl_loop()

            # Save results
            if output_path:
                self._save_results(output_path)

            return {
                "season_id": self.state.season_id,
                "visited_urls": len(self.state.visited_urls),
                "discovered_mutations": len(self.state.discovered_mutations),
                "network_captures": len(self.state.network_captures),
                "external_links": len(self.state.external_links),
                "errors": len(self.state.error_urls),
            }

        finally:
            if self.session:
                self.session.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the season spider.

    :param argv: Command-line arguments (defaults to sys.argv[1:])
    :returns: Exit code (0 = success, non-zero = error)
    """
    parser = argparse.ArgumentParser(
        description="Spider all GET-traversable paths and mutations for a GameSheet season.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Spider season 15020 with default output
    %(prog)s 15020

    # Spider with custom output path
    %(prog)s 15020 -o /tmp/season-15020-mapping.json

    # Use custom browser executable (Fedora Chromium)
    %(prog)s 15020 --browser /usr/bin/chromium-browser

    # Run in non-headless mode for debugging
    %(prog)s 15020 --no-headless -v

Environment variables:
    GAMESHEET_USERNAME    - GameSheet account email
    GAMESHEET_PASSWORD    - GameSheet account password
    GAMESHEET_BASE_URL    - Base URL (default: https://gamesheet.app)
        """,
    )

    parser.add_argument(
        "season_id",
        help="Season ID to spider (e.g., 15020)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON file path (default: season-{id}-spider.json in current directory)",
    )
    parser.add_argument(
        "--browser",
        help="Path to browser executable (e.g., /usr/bin/chromium-browser)",
    )
    parser.add_argument(
        "--base-url",
        help="Override base URL (default: https://gamesheet.app)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in non-headless mode (visible window)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be repeated: -v, -vv)",
    )

    args = parser.parse_args(argv)

    # Configure logging
    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Build config
    config_kwargs = {}
    if args.base_url:
        config_kwargs["base_url"] = args.base_url
    if args.no_headless:
        config_kwargs["browser_headless"] = False

    config = Config(**config_kwargs)

    # Validate credentials
    if not config.username or not config.password:
        _LOGGER.error(
            "Authentication credentials required. Set GAMESHEET_USERNAME and GAMESHEET_PASSWORD "
            "environment variables."
        )
        return 1

    # Determine output path
    output_path = args.output or Path(f"season-{args.season_id}-spider.json")

    # Initialize and run spider
    spider = SeasonSpider(
        season_id=args.season_id,
        config=config,
        browser_executable=args.browser,
    )

    try:
        results = spider.run(output_path=output_path)
        _LOGGER.info("Spider completed successfully")
        _LOGGER.info("Results: %s", results)
        return 0

    except KeyboardInterrupt:
        _LOGGER.warning("Spider interrupted by user")
        return 130

    except Exception:  # noqa: BLE001
        _LOGGER.exception("Spider failed with unhandled exception")
        return 1


if __name__ == "__main__":
    sys.exit(main())

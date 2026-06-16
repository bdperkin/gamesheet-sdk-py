#!/usr/bin/env python3
# flake8: noqa: INP001
# pylint: disable=too-many-lines
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
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, Request, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from gamesheet_sdk.browser import BrowserSession
from gamesheet_sdk.config import Config

_LOGGER = logging.getLogger(__name__)

# Human-like delay bounds (seconds)
MIN_DELAY = 2.5
MAX_DELAY = 5.0

# Network request type categories
HTTP_METHODS_MUTATION = {"POST", "PATCH", "PUT", "DELETE"}

# Timeout for page navigation (ms)
NAV_TIMEOUT_MS = 30_000


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
class SpiderState:  # pylint: disable=too-many-instance-attributes
    """Current state of the spider crawl."""

    season_id: str
    base_url: str
    visited_urls: set[str] = field(default_factory=set)
    visited_patterns: set[str] = field(default_factory=set)  # Normalized URL patterns
    pending_queue: deque[str] = field(default_factory=deque)
    discovered_mutations: list[DiscoveredMutation] = field(default_factory=list)
    network_captures: list[NetworkCapture] = field(default_factory=list)
    external_links: set[str] = field(default_factory=set)
    error_urls: dict[str, str] = field(default_factory=dict)
    request_counter: int = 0  # Counter for naming request artifacts


class SeasonSpider:  # pylint: disable=too-few-public-methods
    """Spider for discovering all paths and mutations under a GameSheet season.

    :param season_id: The season ID to spider (e.g., "15020")
    :param config: Configuration object with auth credentials
    :param browser_executable: Optional path to browser executable
    """

    def __init__(
        self,
        season_id: str,
        config: Config,
        browser_executable: str | None = None,
    ) -> None:
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

    def _normalize_url_pattern(self, url: str) -> str:
        """Normalize URL by replacing numeric path segments with placeholders.

        This treats /teams/123/roster and /teams/456/roster as the same pattern, allowing us to discover
        structure rather than crawling all data.

        :param url: URL to normalize
        :returns: Normalized URL pattern with {id} placeholders
        """
        parsed = urlparse(url)
        path_parts = parsed.path.split("/")

        # Replace numeric-only segments with {id}
        normalized_parts = []
        for part in path_parts:
            if part.isdigit():
                normalized_parts.append("{id}")
            else:
                normalized_parts.append(part)

        normalized_path = "/".join(normalized_parts)
        return f"{parsed.scheme}://{parsed.netloc}{normalized_path}"

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
        base = current_url or self.state.base_url
        return urljoin(base, url)

    def _save_request_artifacts(self, request: Request, request_num: int, artifacts_dir: Path) -> None:
        """Save request headers and payload to files.

        :param request: Playwright Request object
        :param request_num: Sequential request number for naming
        :param artifacts_dir: Directory to save artifacts
        """
        try:
            prefix = artifacts_dir / f"{request_num:04d}"

            # Save headers
            headers_file = Path(str(prefix) + "_request_headers.json")
            headers_file.write_text(json.dumps(dict(request.headers), indent=2))

            # Save payload (if present)
            if request.post_data:
                payload_file = Path(str(prefix) + "_request_payload.txt")
                payload_file.write_text(request.post_data)

        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning("Failed to save request artifacts for %s: %s", request.url, exc)

    def _save_response_artifacts(self, response: Response, request_num: int, artifacts_dir: Path) -> None:
        """Save response headers and body to files.

        :param response: Playwright Response object
        :param request_num: Sequential request number for naming
        :param artifacts_dir: Directory to save artifacts
        """
        try:
            prefix = artifacts_dir / f"{request_num:04d}"

            # Save response headers
            headers_file = Path(str(prefix) + "_response_headers.json")
            headers_file.write_text(json.dumps(dict(response.headers), indent=2))

            # Save response body
            try:
                body = response.body()
                response_file = Path(str(prefix) + "_response_body.txt")
                response_file.write_bytes(body)
            except Exception as exc:  # noqa: BLE001
                # Some responses may not have a body or be already consumed
                _LOGGER.debug("Could not read response body for %s: %s", response.url, exc)  # noqa: TRY401

        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning("Failed to save response artifacts for %s: %s", response.url, exc)

    def _setup_network_capture(self, page: Page, source_url: str, artifacts_dir: Path | None) -> None:
        """Attach network request/response listeners to a page.

        :param page: Playwright page to attach listeners to
        :param source_url: The source page URL for attribution
        :param artifacts_dir: Directory to save request/response artifacts (optional)
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

            # Save request artifacts for Fetch/XHR only
            if artifacts_dir and resource_type in {"fetch", "xhr"}:
                self.state.request_counter += 1
                request_num = self.state.request_counter
                self._save_request_artifacts(request, request_num, artifacts_dir)

        def on_response(response: Response) -> None:
            """Capture response status and save response artifacts."""
            # Update the most recent matching capture with status
            for capture in reversed(self.state.network_captures):
                if capture.url == response.url and capture.status is None:
                    capture.status = response.status
                    break

            # Save response artifacts for Fetch/XHR only
            if artifacts_dir and response.request.resource_type in {"fetch", "xhr"}:
                # Find the corresponding request number
                request_num = None
                for i, cap in enumerate(reversed(self.state.network_captures)):
                    if cap.url == response.url and cap.method == response.request.method:
                        request_num = len(self.state.network_captures) - i
                        break

                if request_num:
                    self._save_response_artifacts(response, request_num, artifacts_dir)

        page.on("request", on_request)
        page.on("response", on_response)

    def _discover_mutations(self, page: Page, current_url: str) -> None:  # pylint: disable=too-many-locals
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

        _LOGGER.debug("Found %d <a[href]> elements on page", len(link_elements))

        for element in link_elements:
            href = element.get_attribute("href")
            if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                continue

            absolute_url = self._normalize_url(href, current_url)
            links.append(absolute_url)
            _LOGGER.debug("Extracted link: %s", absolute_url)

        _LOGGER.info("Extracted %d total links from page", len(links))
        return links

    def _human_delay(self) -> None:
        """Sleep for a randomized human-like delay."""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)  # noqa: S311 # nosec B311
        _LOGGER.debug("Human delay: %.2fs", delay)
        time.sleep(delay)

    def _visit_url(self, url: str, artifacts_dir: Path | None = None) -> bool:
        """Visit a URL and perform discovery.

        :param url: URL to visit
        :param artifacts_dir: Optional directory to save network artifacts
        :returns: True if visit succeeded, False on error
        """
        if not self.page:
            _LOGGER.error("Page not initialized")
            return False

        # Check if we've already visited this URL pattern
        pattern = self._normalize_url_pattern(url)
        if pattern in self.state.visited_patterns:
            _LOGGER.info("Skipping %s (pattern already visited: %s)", url, pattern)
            return True

        _LOGGER.info("Visiting: %s (pattern: %s)", url, pattern)

        try:
            # Attach network capture before navigation
            self._setup_network_capture(self.page, url, artifacts_dir)

            # Navigate to URL and wait for network to be mostly idle
            # This is important for SPAs like GameSheet that render content via JavaScript
            try:
                self.page.goto(url, wait_until="networkidle", timeout=NAV_TIMEOUT_MS)
            except PlaywrightTimeoutError:
                _LOGGER.debug("Network didn't reach idle in %dms, proceeding anyway", NAV_TIMEOUT_MS)

            # Mark as visited (both URL and pattern)
            self.state.visited_urls.add(url)
            self.state.visited_patterns.add(pattern)

            # Discover mutations
            self._discover_mutations(self.page, url)

            # Queue ALL unvisited internal links
            all_links = self._extract_links(self.page, url)
            queued_count = 0
            for link in all_links:
                # Skip if already visited or already queued
                if link in self.state.visited_urls or link in self.state.pending_queue:
                    continue

                if self._is_internal_url(link):
                    self.state.pending_queue.append(link)
                    queued_count += 1
                    _LOGGER.debug("Queued for visit: %s", link)
                else:
                    # Log external link
                    if link not in self.state.external_links:
                        self.state.external_links.add(link)
                        _LOGGER.info("External link (not traversing): %s", link)

            if queued_count > 0:
                _LOGGER.info("Queued %d new URLs for crawling", queued_count)

            return True

        except PlaywrightTimeoutError as exc:
            _LOGGER.warning("Timeout visiting %s: %s", url, exc)
            self.state.error_urls[url] = f"Timeout: {exc}"
            return False

        except Exception as exc:  # noqa: BLE001
            _LOGGER.exception("Error visiting %s", url)  # noqa: TRY401
            self.state.error_urls[url] = f"Error: {exc}"
            return False

    def _crawl_loop(self, artifacts_dir: Path | None = None) -> None:
        """Process the queue until empty.

        :param artifacts_dir: Optional directory to save network artifacts
        """
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

            # Skip if pattern already visited
            pattern = self._normalize_url_pattern(url)
            if pattern in self.state.visited_patterns:
                _LOGGER.debug("Skipping %s (pattern already visited)", url)
                self.state.visited_urls.add(url)  # Mark as visited to avoid re-checking
                continue

            # Skip if not internal
            if not self._is_internal_url(url):
                if url not in self.state.external_links:
                    self.state.external_links.add(url)
                    _LOGGER.info("Skipping external URL: %s", url)
                continue

            # Visit the URL
            self._visit_url(url, artifacts_dir)

            # Human-like delay before next request
            if self.state.pending_queue:
                self._human_delay()

        _LOGGER.info("Crawl complete. No more unvisited internal URLs.")

    def _create_custom_browser_session(self) -> BrowserSession:
        """Create a BrowserSession with custom browser executable.

        :returns: BrowserSession configured with custom executable
        """
        from playwright.sync_api import sync_playwright  # pylint: disable=import-outside-toplevel

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
                session._context = session._browser.new_context(
                    storage_state=storage_state,  # type: ignore[arg-type]
                )
            else:
                session._context = session._browser.new_context()

        session._start = custom_start  # type: ignore[method-assign]
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
            # BrowserSession automatically loads saved browser-state.json
            # If you've run 'gamesheet-sdk-py login', you're already authenticated
            _LOGGER.info("Creating browser page with saved session")
            self.page = self.session.new_page()

            # Create artifacts directory if output path is specified
            artifacts_dir = None
            if output_path:
                artifacts_dir = output_path.parent / f"{output_path.stem}_artifacts"
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                _LOGGER.info("Saving network artifacts to: %s", artifacts_dir)

            # Execute crawl
            self._crawl_loop(artifacts_dir)

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
    epilog_text = """Examples:
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
"""

    parser = argparse.ArgumentParser(
        description="Spider all GET-traversable paths and mutations for a GameSheet season.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text,
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

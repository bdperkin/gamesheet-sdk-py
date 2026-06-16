# Spider Testing Plan

This document outlines the testing strategy for the `spider_season.py` utility.

## Unit Testing Strategy

### Core Components to Test

1. **URL Normalization** (`_normalize_url`)

   - Relative URLs
   - Absolute URLs
   - Fragment removal
   - Base URL resolution

2. **Internal URL Detection** (`_is_internal_url`)

   - Season-scoped URLs (should return True)
   - External URLs (should return False)
   - Edge cases (subdomains, protocols)

3. **Link Extraction** (`_extract_links`)

   - Standard `<a>` tags
   - JavaScript/mailto/tel links (should be filtered)
   - Relative vs absolute hrefs

4. **Mutation Discovery** (`_discover_mutations`)

   - Form method detection (POST/PATCH/DELETE)
   - Data-method attributes
   - CSS class heuristics
   - Button type="submit" detection

### Mock Testing Approach

```python
# Example unit test structure
import pytest
from unittest.mock import Mock, MagicMock
from scripts.spider_season import SeasonSpider, SpiderState
from gamesheet_sdk.config import Config


@pytest.fixture
def spider():
    """Create a spider instance for testing."""
    config = Config(
        username="test@example.com",
        password="test-password",  # nosec
        browser_headless=True,
    )
    return SeasonSpider(season_id="15020", config=config)


def test_normalize_url_absolute(spider):
    """Test normalization of absolute URLs."""
    url = "https://gamesheet.app/seasons/15020/teams"
    result = spider._normalize_url(url)
    assert result == url


def test_normalize_url_relative(spider):
    """Test normalization of relative URLs."""
    current = "https://gamesheet.app/seasons/15020"
    relative = "./teams"
    result = spider._normalize_url(relative, current)
    assert result == "https://gamesheet.app/seasons/15020/teams"


def test_normalize_url_removes_fragment(spider):
    """Test that URL fragments are removed."""
    url = "https://gamesheet.app/seasons/15020/teams#section"
    result = spider._normalize_url(url)
    assert "#" not in result
    assert result == "https://gamesheet.app/seasons/15020/teams"


def test_is_internal_url_season_path(spider):
    """Test internal URL detection for season paths."""
    internal = "https://gamesheet.app/seasons/15020/divisions"
    assert spider._is_internal_url(internal) is True


def test_is_internal_url_external(spider):
    """Test internal URL detection for external links."""
    external = "https://help.gamesheet.app/docs"
    assert spider._is_internal_url(external) is False


def test_is_internal_url_different_season(spider):
    """Test that different season IDs are considered external."""
    other_season = "https://gamesheet.app/seasons/99999"
    assert spider._is_internal_url(other_season) is False
```

## Integration Testing

### Test Scenarios

#### 1. Authentication Flow

- Valid credentials → successful login
- Invalid credentials → AuthenticationError
- Existing session → reuses saved state

#### 2. Page Navigation

- Valid URL → page loads successfully
- Invalid URL → error logged, crawl continues
- Network timeout → error logged, crawl continues

#### 3. Link Discovery

- Simple anchor tags → extracted correctly
- Relative links → normalized to absolute
- External links → logged but not queued
- JavaScript links → filtered out

#### 4. Mutation Discovery

- POST form → captured with correct method
- DELETE button with data-method → captured
- CSS class-based detection → captured
- Submit button within form → form action captured

#### 5. Network Capture

- Fetch requests → captured with metadata
- XHR requests → captured with metadata
- Response status → recorded correctly
- Source page attribution → accurate

#### 6. Queue Management

- Initial URL added → crawl starts
- New links found → added to queue
- Already visited → not re-queued
- External links → never queued

#### 7. Result Persistence

- Output file created → valid JSON
- All sections populated → correct structure
- Summary accurate → matches actual counts

### Integration Test Approach

```python
@pytest.mark.browser
@pytest.mark.vcr
def test_spider_basic_flow(tmp_path):
    """Test a basic spider crawl with VCR cassette."""
    config = Config(
        username=os.getenv("GAMESHEET_USERNAME"),
        password=os.getenv("GAMESHEET_PASSWORD"),
        browser_headless=True,
    )

    spider = SeasonSpider(season_id="15020", config=config)
    output_path = tmp_path / "test-spider.json"

    results = spider.run(output_path=output_path)

    # Verify results
    assert results["visited_urls"] > 0
    assert results["discovered_mutations"] >= 0
    assert results["network_captures"] > 0

    # Verify output file
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert data["season_id"] == "15020"
    assert "summary" in data
```

## Manual Testing Checklist

### Pre-Flight Checks

- [ ] Playwright installed: `python -m playwright install chromium`
- [ ] SDK installed: `pip install -e ".[all]"`
- [ ] Credentials set: `GAMESHEET_USERNAME`, `GAMESHEET_PASSWORD`
- [ ] Scripts executable: `chmod +x scripts/*.{py,sh}`

### Basic Functionality

- [ ] Run with minimal args: `./scripts/spider_season.py 15020`
- [ ] Output file created with expected name
- [ ] Output file contains valid JSON
- [ ] Summary section shows non-zero counts
- [ ] Visited URLs list populated
- [ ] No mutations were actually executed (verify in GameSheet UI)

### Verbose Mode

- [ ] Run with `-v`: see INFO-level logs
- [ ] Run with `-vv`: see DEBUG-level logs
- [ ] Network captures visible in debug output
- [ ] Human delays visible in logs
- [ ] Page visits logged with URLs

### Non-Headless Mode

- [ ] Run with `--no-headless`: browser window opens
- [ ] Can observe navigation in real-time
- [ ] Login flow visible
- [ ] Page-to-page navigation visible
- [ ] No errors in browser console (check DevTools)

### Custom Output Path

- [ ] Run with `-o /tmp/test.json`
- [ ] Output created at specified path
- [ ] Directory created if needed

### Custom Browser

- [ ] Run with `--browser /usr/bin/chromium-browser`
- [ ] Logs show custom browser path
- [ ] Browser launches successfully
- [ ] Crawl completes normally

### Error Handling

- [ ] Invalid season ID: appropriate error handling
- [ ] Missing credentials: clear error message
- [ ] Network timeout: logged and continues
- [ ] Invalid URL: logged and continues

### Safety Verification

- [ ] No data deleted (check GameSheet UI)
- [ ] No data modified (check GameSheet UI)
- [ ] No data created (check GameSheet UI)
- [ ] Only GET requests in browser DevTools Network tab
- [ ] POST/PATCH/DELETE only in discovered_mutations, not executed

### Output Validation

- [ ] `visited_urls`: all URLs start with base_url
- [ ] `discovered_mutations`: contain method, url, element info
- [ ] `network_captures`: contain URL, method, status
- [ ] `external_links`: contain URLs outside season scope
- [ ] `error_urls`: empty or contain only timeout/error cases
- [ ] `summary`: counts match array lengths

### Edge Cases

- [ ] Season with no divisions: handles gracefully
- [ ] Season with no games: handles gracefully
- [ ] Season with no teams: handles gracefully
- [ ] Already authenticated (cached session): skips login
- [ ] Interrupted with Ctrl+C: saves partial results

### Performance

- [ ] Delays between requests: 2.5-5 seconds observed
- [ ] Network settle timeout: ~3 seconds observed
- [ ] Navigation timeout: ~30 seconds max per page
- [ ] Total runtime reasonable: ~5-10 min for typical season

### Wrapper Script

- [ ] `./scripts/spider_example.sh 15020`: runs successfully
- [ ] Creates `spider-results/` directory
- [ ] Output file in correct location
- [ ] With `GAMESHEET_BROWSER` env var: uses custom browser

## Automated Testing TODO

Future automated tests to add:

1. URL Utilities Suite

   - `test_normalize_url_*`
   - `test_is_internal_url_*`
   - `test_extract_links_*`

2. Mutation Discovery Suite

   - `test_discover_form_mutations`
   - `test_discover_button_mutations`
   - `test_discover_data_method_attributes`
   - `test_discover_css_class_heuristics`

3. Network Capture Suite

   - `test_capture_fetch_requests`
   - `test_capture_xhr_requests`
   - `test_capture_response_status`
   - `test_capture_source_attribution`

4. Crawl Logic Suite

   - `test_queue_management`
   - `test_visited_tracking`
   - `test_external_link_filtering`
   - `test_human_delay_range`

5. Integration Suite

   - `test_full_crawl_small_season` (with VCR)
   - `test_authentication_flow`
   - `test_output_file_format`
   - `test_error_recovery`

6. Safety Suite

   - `test_no_mutations_executed`
   - `test_only_get_requests_made`
   - `test_forms_not_submitted`
   - `test_buttons_not_clicked`

## Continuous Integration

Suggested CI workflow:

```yaml
name: Spider Tests

on:
  pull_request:
    paths:
      - 'scripts/spider_season.py'
      - 'tests/test_spider_*.py'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[all]"
          python -m playwright install chromium

      - name: Run spider unit tests
        run: pytest tests/test_spider_*.py -v

      - name: Run spider integration tests
        env:
          GAMESHEET_USERNAME: ${{ secrets.GAMESHEET_USERNAME }}
          GAMESHEET_PASSWORD: ${{ secrets.GAMESHEET_PASSWORD }}
        run: pytest tests/test_spider_*.py -v -m integration
```

## Test Data

### Safe Test Season IDs

- Use a dedicated test season with minimal data
- Coordinate with GameSheet team for test accounts
- Alternatively, use VCR cassettes for deterministic replay

### VCR Configuration

```python
# In tests/conftest.py
import pytest


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["authorization", "cookie"],
        "filter_query_parameters": ["token", "key"],
        "record_mode": "once",
    }
```

## Known Limitations to Test

1. **SPA Navigation**: May miss client-side route changes
2. **Dynamic Forms**: Forms added via JS after page load
3. **Auth-Gated Paths**: Paths requiring additional permissions
4. **Infinite Scroll**: Content loaded on scroll events
5. **Modal Dialogs**: Hidden mutation buttons in modals

## Success Criteria

A successful test run should demonstrate:

- ✅ No data modified/deleted/created in GameSheet
- ✅ All visited URLs are internal to season scope
- ✅ Network captures include Fetch/XHR requests
- ✅ Mutations discovered but not executed
- ✅ Output JSON is valid and complete
- ✅ Human-like delays observed (2.5-5s)
- ✅ External links logged but not followed
- ✅ Errors handled gracefully without crashes

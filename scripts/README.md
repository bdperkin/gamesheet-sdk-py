# Utility Scripts

This directory contains utility scripts that leverage the GameSheet SDK for various tasks.

## spider_season.py

A comprehensive web spider that discovers all GET-traversable paths and mutation operations for a GameSheet season.

### Features

- **Safe Discovery**: Only executes GET requests; discovers but never executes POST/PATCH/DELETE operations
- **Network Capture**: Records all Fetch/XHR requests made during traversal
- **Human-Like Behavior**: Randomized 2.5-5 second delays between requests
- **Comprehensive Mapping**: Generates detailed JSON output with all discovered paths and operations
- **Auth Integration**: Leverages existing SDK authentication infrastructure
- **External Link Detection**: Logs but doesn't traverse links outside the season URL scope

### Safety Guarantees

The spider is designed to be **completely read-only**:

1. ✅ **Only GET requests are executed** - All navigation uses safe HTTP methods
2. ✅ **Mutations are discovered but never invoked** - POST/PATCH/DELETE operations are recorded without execution
3. ✅ **No forms are submitted** - Forms are analyzed but not submitted
4. ✅ **No buttons are clicked** - Mutation buttons are detected via DOM inspection only
5. ✅ **External links are logged only** - Links outside the season scope are recorded but not followed

### Usage

#### Basic Usage

```bash
# Set credentials
export GAMESHEET_USERNAME="your-email@example.com"
export GAMESHEET_PASSWORD="your-password"

# Spider a season
./scripts/spider_season.py 15020
```

This will:
1. Authenticate using your credentials
2. Spider all paths under `https://gamesheet.app/seasons/15020`
3. Save results to `season-15020-spider.json` in the current directory

#### Advanced Options

```bash
# Custom output location
./scripts/spider_season.py 15020 -o /tmp/my-spider-results.json

# Use Fedora native Chromium browser
./scripts/spider_season.py 15020 --browser /usr/bin/chromium-browser

# Run in visible mode for debugging
./scripts/spider_season.py 15020 --no-headless -v

# Maximum verbosity (debug logging)
./scripts/spider_season.py 15020 -vv
```

#### All Options

```
usage: spider_season.py [-h] [-o OUTPUT] [--browser BROWSER] [--base-url BASE_URL]
                        [--no-headless] [-v]
                        season_id

positional arguments:
  season_id             Season ID to spider (e.g., 15020)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output JSON file path (default: season-{id}-spider.json)
  --browser BROWSER     Path to browser executable (e.g., /usr/bin/chromium-browser)
  --base-url BASE_URL   Override base URL (default: https://gamesheet.app)
  --no-headless         Run browser in non-headless mode (visible window)
  -v, --verbose         Increase verbosity (can be repeated: -v, -vv)
```

### Output Format

The spider generates a JSON file with the following structure:

```json
{
  "season_id": "15020",
  "base_url": "https://gamesheet.app/seasons/15020",
  "crawl_timestamp": 1718467200.0,
  "summary": {
    "visited_urls": 42,
    "discovered_mutations": 15,
    "network_captures": 127,
    "external_links": 3,
    "errors": 0
  },
  "visited_urls": [
    "https://gamesheet.app/seasons/15020",
    "https://gamesheet.app/seasons/15020/divisions",
    "https://gamesheet.app/seasons/15020/teams",
    ...
  ],
  "discovered_mutations": [
    {
      "method": "DELETE",
      "url": "https://gamesheet.app/api/teams/123",
      "element_type": "button",
      "element_text": "Delete Team",
      "form_action": null,
      "discovered_from_url": "https://gamesheet.app/seasons/15020/teams/123"
    },
    ...
  ],
  "network_captures": [
    {
      "url": "https://gamesheet.app/api/seasons/15020/divisions",
      "method": "GET",
      "resource_type": "fetch",
      "status": 200,
      "source_page": "https://gamesheet.app/seasons/15020/divisions"
    },
    ...
  ],
  "external_links": [
    "https://help.gamesheet.app/docs",
    ...
  ],
  "error_urls": {}
}
```

### How It Works

1. **Authentication**: Uses the SDK's `login()` function to authenticate via browser
2. **Queue-Based Traversal**: Maintains a queue of URLs to visit, starting with the season base URL
3. **Network Monitoring**: Attaches Playwright listeners to capture all Fetch/XHR requests
4. **DOM Inspection**: Analyzes page DOM to discover:
   - Clickable links (for GET traversal)
   - Forms with mutation methods (POST/PATCH/DELETE)
   - Buttons/links with mutation intent (via data attributes and CSS classes)
5. **Link Extraction**: Finds all `<a>` elements and normalizes their URLs
6. **Smart Queueing**: Only queues internal, unvisited URLs for traversal
7. **Human Delay**: Waits 2.5-5 seconds (randomized) between requests
8. **Result Persistence**: Saves comprehensive mapping to JSON

### Mutation Discovery Heuristics

The spider discovers mutations through several strategies:

1. **Form Method Inspection**: Analyzes `<form method="...">` attributes
2. **Data Attributes**: Detects `data-method`, `data-action` attributes
3. **CSS Classes**: Recognizes patterns like `.btn-delete`, `.remove-btn`
4. **Submit Buttons**: Tracks `<button type="submit">` within forms
5. **Semantic Analysis**: Interprets element text for mutation keywords

## analyze_spider_output.py

A companion utility for analyzing spider output files and extracting insights.

### Features

- **Summary Statistics**: Overview of crawl results
- **Mutation Analysis**: Breakdown by HTTP method and element type
- **Network Analysis**: Resource types, API endpoints, status codes
- **URL Analysis**: Path depth distribution, common prefixes
- **Error Analysis**: Grouping and categorization of errors
- **Data Export**: Extract API endpoints and mutations to separate files

### Usage

#### Basic Analysis

```bash
# Analyze a spider output file
./scripts/analyze_spider_output.py season-15020-spider.json
```

Output includes:
- Summary statistics
- Mutation breakdown by method and type
- Network captures by resource type and method
- Unique API endpoints
- HTTP status code distribution
- URL depth distribution
- Error analysis (if any)

#### Export API Endpoints

```bash
# Extract all unique API endpoints to a text file
./scripts/analyze_spider_output.py season-15020-spider.json \
  --export-apis api-endpoints.txt
```

#### Export Mutations

```bash
# Extract discovered mutations to a separate JSON file
./scripts/analyze_spider_output.py season-15020-spider.json \
  --export-mutations mutations.json
```

#### Combined Export

```bash
# Export both APIs and mutations, skip console output
./scripts/analyze_spider_output.py season-15020-spider.json \
  --export-apis apis.txt \
  --export-mutations mutations.json \
  --no-summary
```

### Example Output

```
======================================================================
Spider Output Analysis - Season 15020
======================================================================
Base URL: https://gamesheet.app/seasons/15020
Crawl Time: 1718467200.123456

Summary Statistics:
----------------------------------------------------------------------
  Visited URLs:              8
  Discovered Mutations:      3
  Network Captures:          4
  External Links:            2
  Errors:                    0

Mutation Analysis:
----------------------------------------------------------------------
  By HTTP Method:
    DELETE      2
    POST        1

  By Element Type:
    button         2
    form           1

  Top 10 Mutation URLs:
     1. (1x) https://gamesheet.app/api/teams/456
     2. (1x) https://gamesheet.app/api/games/789
     3. (1x) https://gamesheet.app/api/divisions

Network Analysis:
----------------------------------------------------------------------
  By Resource Type:
    fetch          3
    xhr            1

  By HTTP Method:
    GET            4

  Unique API Endpoints (4):
     1. (  1x) https://gamesheet.app/api/games?season_id=15020&status=scheduled
     2. (  1x) https://gamesheet.app/api/seasons/15020
     3. (  1x) https://gamesheet.app/api/seasons/15020/divisions
     4. (  1x) https://gamesheet.app/api/teams?season_id=15020
```

### Example Files

- **`spider_example.sh`**: Convenience wrapper script demonstrating common usage patterns
- **`analyze_spider_output.py`**: Analysis and export utility for spider results
- **`example-output.json`**: Sample output showing the structure of discovered data

### Limitations

- **JavaScript-heavy mutations**: Mutations triggered purely via JavaScript event handlers (without DOM attributes) may not be detected
- **Dynamic content**: Content loaded after network idle timeout may be missed
- **Login-gated paths**: Paths requiring additional authentication beyond the initial login may not be accessible
- **SPA Navigation**: Single-Page Application navigation that doesn't update the URL may not be fully captured

### Development Notes

The spider leverages existing SDK components:

- `gamesheet_sdk.browser.BrowserSession` - Playwright session management
- `gamesheet_sdk.auth.login` - Authentication flow
- `gamesheet_sdk.config.Config` - Configuration and credential resolution

All behavior is designed to be **maximally safe** - when in doubt, the spider errs on the side of not executing an action.

### Troubleshooting

#### Authentication Issues

```bash
# Verify credentials are set
echo $GAMESHEET_USERNAME
echo $GAMESHEET_PASSWORD  # Shows length, not actual password

# Run with verbose logging
./scripts/spider_season.py 15020 -vv
```

#### Network Timeouts

```bash
# Run in visible mode to see what's happening
./scripts/spider_season.py 15020 --no-headless -v
```

#### Custom Browser Path

If you need to use a system-installed browser (e.g., Fedora Chromium):

```bash
# Use the --browser flag with the executable path
./scripts/spider_season.py 15020 --browser /usr/bin/chromium-browser

# Or set via environment variable and use the example wrapper
export GAMESHEET_BROWSER=/usr/bin/chromium-browser
./scripts/spider_example.sh 15020
```

### Future Enhancements

Potential improvements for future iterations:

- [ ] Full integration of custom browser executable path
- [ ] Parallel crawling with configurable concurrency
- [ ] Resume capability from partial crawl state
- [ ] Screenshot capture for each visited page
- [ ] GraphQL/REST API endpoint detection
- [ ] Form field analysis (input types, validation)
- [ ] Export to additional formats (CSV, GraphML, DOT)
- [ ] Visualization of discovered paths (graph/tree view)

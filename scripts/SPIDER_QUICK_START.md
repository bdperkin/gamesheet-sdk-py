# Spider Quick Start Guide

Quick reference for using the GameSheet season spider utility.

## Prerequisites

```bash
# 1. Install the SDK with playwright support
pip install -e ".[all]"

# 2. Install Playwright browsers
python -m playwright install chromium

# 3. Set credentials
export GAMESHEET_USERNAME="your-email@example.com"
export GAMESHEET_PASSWORD="your-password"
```

## Common Commands

### Basic Spider Run

```bash
# Spider season 15020 with default settings
./scripts/spider_season.py 15020
```

**Output**: `season-15020-spider.json` in current directory

### Custom Output Location

```bash
./scripts/spider_season.py 15020 -o /tmp/my-results.json
```

### Verbose Mode (Recommended)

```bash
# See what's happening in real-time
./scripts/spider_season.py 15020 -v
```

### Debug Mode (Maximum Verbosity)

```bash
# See everything including network captures
./scripts/spider_season.py 15020 -vv
```

### Non-Headless (Visual Browser)

```bash
# Watch the browser navigate (useful for debugging)
./scripts/spider_season.py 15020 --no-headless -v
```

### Custom Browser (Fedora Chromium)

```bash
./scripts/spider_season.py 15020 --browser /usr/bin/chromium-browser
```

### Using the Convenience Wrapper

```bash
# Spider with example script (handles output directory)
./scripts/spider_example.sh 15020 ./my-results

# With custom browser
export GAMESHEET_BROWSER=/usr/bin/chromium-browser
./scripts/spider_example.sh 15020
```

## Understanding the Output

The spider generates a JSON file with four main sections:

### 1. Visited URLs

All GET-traversable paths discovered under the season URL.

```json
"visited_urls": [
  "https://gamesheet.app/seasons/15020",
  "https://gamesheet.app/seasons/15020/divisions",
  "https://gamesheet.app/seasons/15020/teams"
]
```

### 2. Discovered Mutations

POST/PATCH/DELETE operations found but **not executed**.

```json
"discovered_mutations": [
  {
    "method": "DELETE",
    "url": "https://gamesheet.app/api/teams/456",
    "element_type": "button",
    "element_text": "Delete Team",
    "discovered_from_url": "https://gamesheet.app/seasons/15020/teams/456"
  }
]
```

### 3. Network Captures

All Fetch/XHR requests captured during traversal.

```json
"network_captures": [
  {
    "url": "https://gamesheet.app/api/seasons/15020/divisions",
    "method": "GET",
    "resource_type": "fetch",
    "status": 200,
    "source_page": "https://gamesheet.app/seasons/15020/divisions"
  }
]
```

### 4. External Links

Links outside the season scope (logged but not followed).

```json
"external_links": [
  "https://help.gamesheet.app/docs"
]
```

## Safety Features

### What the Spider DOES

✅ Executes GET requests only ✅ Discovers forms and mutation buttons ✅ Captures network requests ✅ Logs external links ✅ Follows internal season links ✅ Uses
randomized human-like delays

### What the Spider DOES NOT DO

❌ Execute POST/PATCH/DELETE requests ❌ Submit forms ❌ Click mutation buttons ❌ Follow external links ❌ Modify any data ❌ Delete any data

## Troubleshooting

### Authentication Failed

```bash
# Verify credentials
echo "Username: $GAMESHEET_USERNAME"
echo "Password set: $([ -n "$GAMESHEET_PASSWORD" ] && echo 'yes' || echo 'no')"

# Try with debug logging
./scripts/spider_season.py 15020 -vv
```

### Browser Not Found

```bash
# Check Playwright installation
python -m playwright install chromium

# Or use system browser
./scripts/spider_season.py 15020 --browser /usr/bin/chromium-browser
```

### Network Timeouts

```bash
# Run in visual mode to see what's happening
./scripts/spider_season.py 15020 --no-headless -v
```

### Permission Denied

```bash
# Make scripts executable
chmod +x scripts/spider_season.py scripts/spider_example.sh
```

## Performance Notes

- **Delay**: 2.5-5 seconds between requests (randomized)
- **Timeout**: 30 seconds per page navigation
- **Network Settle**: 3 seconds wait after page load
- **Typical Runtime**: 5-10 minutes for ~50 pages

## Analyzing Results

After running the spider, use the analysis tool for insights:

### Quick Analysis

```bash
# Full analysis with all statistics
./scripts/analyze_spider_output.py season-15020-spider.json
```

### Extract API Endpoints

```bash
# Get a list of all unique API endpoints
./scripts/analyze_spider_output.py season-15020-spider.json \
  --export-apis api-endpoints.txt

# View the endpoints
cat api-endpoints.txt
```

### Extract Mutations

```bash
# Export just the mutations to a separate file
./scripts/analyze_spider_output.py season-15020-spider.json \
  --export-mutations mutations.json

# View mutations by method
jq '.[] | select(.method == "DELETE")' mutations.json
```

## Next Steps

After running the spider:

1. **Review Output**: Check the JSON file for discovered paths
2. **Run Analysis**: Use `analyze_spider_output.py` for insights
3. **Analyze Mutations**: Examine discovered POST/PATCH/DELETE operations
4. **Network Analysis**: Review captured API endpoints
5. **Documentation**: Use findings to document the WebUI structure

## Example Workflow

```bash
# 1. Set credentials
export GAMESHEET_USERNAME="user@example.com"
export GAMESHEET_PASSWORD="secret"

# 2. Create results directory
mkdir -p spider-results

# 3. Run spider with verbose output
./scripts/spider_season.py 15020 \
  -o spider-results/season-15020.json \
  -v

# 4. Review results
jq '.summary' spider-results/season-15020.json

# 5. Extract discovered mutations
jq '.discovered_mutations' spider-results/season-15020.json

# 6. List all visited URLs
jq '.visited_urls[]' spider-results/season-15020.json
```

## Advanced Usage

### Extracting Specific Data

```bash
# Count mutations by method
jq '.discovered_mutations | group_by(.method) | map({method: .[0].method, count: length})' result.json

# List all API endpoints
jq '.network_captures | map(.url) | unique | sort' result.json

# Find all DELETE operations
jq '.discovered_mutations | map(select(.method == "DELETE"))' result.json
```

### Comparing Multiple Seasons

```bash
# Spider multiple seasons
for season in 15020 15021 15022; do
  ./scripts/spider_season.py $season -o results/season-$season.json -v
done

# Compare mutation counts
for f in results/*.json; do
  echo "$f: $(jq '.summary.discovered_mutations' $f) mutations"
done
```

## See Also

- **`README.md`**: Full documentation with implementation details
- **`spider_season.py`**: Source code with inline documentation
- **`example-output.json`**: Sample output structure
- **`spider_example.sh`**: Convenience wrapper script

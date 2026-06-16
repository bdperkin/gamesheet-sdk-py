#!/bin/bash
# Example usage of spider_season.py
#
# This script demonstrates common usage patterns for the season spider.

set -euo pipefail

# Configuration
SEASON_ID="${1:-15020}"
OUTPUT_DIR="${2:-./spider-results}"
BROWSER="${GAMESHEET_BROWSER:-}"  # Optional: /usr/bin/chromium-browser

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check for credentials
if [[ -z "${GAMESHEET_USERNAME:-}" ]] || [[ -z "${GAMESHEET_PASSWORD:-}" ]]; then
    echo "Error: GAMESHEET_USERNAME and GAMESHEET_PASSWORD must be set" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  export GAMESHEET_USERNAME='your-email@example.com'" >&2
    echo "  export GAMESHEET_PASSWORD='your-password'" >&2
    echo "  $0 $SEASON_ID" >&2
    exit 1
fi

# Build command
CMD=(
    "$(dirname "$0")/spider_season.py"
    "$SEASON_ID"
    -o "$OUTPUT_DIR/season-${SEASON_ID}-spider.json"
    -v
)

# Add browser if specified
if [[ -n "$BROWSER" ]]; then
    CMD+=(--browser "$BROWSER")
fi

# Run spider
echo "Spidering season $SEASON_ID..."
echo "Output: $OUTPUT_DIR/season-${SEASON_ID}-spider.json"
echo ""

"${CMD[@]}"

echo ""
echo "Spider complete! Results saved to:"
echo "  $OUTPUT_DIR/season-${SEASON_ID}-spider.json"

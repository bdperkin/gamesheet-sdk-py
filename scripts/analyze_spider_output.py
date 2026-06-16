#!/usr/bin/env python3
"""Analyze and summarize spider output JSON files.

This utility provides quick analysis and insights from spider crawl results,
including statistics, mutation summaries, and API endpoint extraction.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def load_spider_output(path: Path) -> dict[str, Any]:
    """Load and validate spider output JSON.

    :param path: Path to spider output JSON file
    :returns: Parsed spider output data
    :raises ValueError: If file is not valid JSON or missing required fields
    """
    if not path.exists():
        raise FileNotFoundError(f"Spider output not found: {path}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    required_fields = ["season_id", "base_url", "summary", "visited_urls"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    return data


def print_summary(data: dict[str, Any]) -> None:
    """Print overview summary statistics.

    :param data: Spider output data
    """
    print("=" * 70)
    print(f"Spider Output Analysis - Season {data['season_id']}")
    print("=" * 70)
    print(f"Base URL: {data['base_url']}")
    print(f"Crawl Time: {data.get('crawl_timestamp', 'N/A')}")
    print()
    print("Summary Statistics:")
    print("-" * 70)

    summary = data["summary"]
    print(f"  Visited URLs:         {summary['visited_urls']:>6}")
    print(f"  Discovered Mutations: {summary['discovered_mutations']:>6}")
    print(f"  Network Captures:     {summary['network_captures']:>6}")
    print(f"  External Links:       {summary['external_links']:>6}")
    print(f"  Errors:               {summary['errors']:>6}")
    print()


def analyze_mutations(data: dict[str, Any]) -> None:
    """Analyze and summarize discovered mutations.

    :param data: Spider output data
    """
    mutations = data.get("discovered_mutations", [])
    if not mutations:
        print("No mutations discovered.")
        print()
        return

    print("Mutation Analysis:")
    print("-" * 70)

    # Count by method
    methods = Counter(m["method"] for m in mutations)
    print("  By HTTP Method:")
    for method, count in methods.most_common():
        print(f"    {method:<8} {count:>6}")
    print()

    # Count by element type
    element_types = Counter(m.get("element_type", "unknown") for m in mutations)
    print("  By Element Type:")
    for elem_type, count in element_types.most_common():
        print(f"    {elem_type:<15} {count:>6}")
    print()

    # Top mutation URLs
    print("  Top 10 Mutation URLs:")
    url_counter = Counter(m["url"] for m in mutations)
    for i, (url, count) in enumerate(url_counter.most_common(10), 1):
        print(f"    {i:2}. ({count:>2}x) {url}")
    print()


def analyze_network(data: dict[str, Any]) -> None:
    """Analyze and summarize network captures.

    :param data: Spider output data
    """
    captures = data.get("network_captures", [])
    if not captures:
        print("No network captures recorded.")
        print()
        return

    print("Network Analysis:")
    print("-" * 70)

    # Count by resource type
    resource_types = Counter(c["resource_type"] for c in captures)
    print("  By Resource Type:")
    for res_type, count in resource_types.most_common():
        print(f"    {res_type:<15} {count:>6}")
    print()

    # Count by HTTP method
    methods = Counter(c["method"] for c in captures)
    print("  By HTTP Method:")
    for method, count in methods.most_common():
        print(f"    {method:<8} {count:>6}")
    print()

    # API endpoints (URLs containing /api/)
    api_endpoints = [c["url"] for c in captures if "/api/" in c["url"]]
    unique_apis = sorted(set(api_endpoints))

    print(f"  Unique API Endpoints ({len(unique_apis)}):")
    for i, endpoint in enumerate(unique_apis[:20], 1):
        count = api_endpoints.count(endpoint)
        print(f"    {i:2}. ({count:>3}x) {endpoint}")
    if len(unique_apis) > 20:
        print(f"    ... and {len(unique_apis) - 20} more")
    print()

    # Status code distribution
    statuses = Counter(c.get("status") for c in captures if c.get("status"))
    if statuses:
        print("  HTTP Status Codes:")
        for status, count in sorted(statuses.items()):
            print(f"    {status:>3} {count:>6}")
        print()


def analyze_urls(data: dict[str, Any]) -> None:
    """Analyze visited URLs.

    :param data: Spider output data
    """
    urls = data.get("visited_urls", [])
    if not urls:
        print("No URLs visited.")
        print()
        return

    print("URL Analysis:")
    print("-" * 70)

    # URL path depth analysis
    base_url = data["base_url"]
    depths = Counter(url[len(base_url) :].count("/") for url in urls)

    print("  URL Depth Distribution:")
    for depth, count in sorted(depths.items()):
        bar = "█" * (count * 40 // max(depths.values()))
        print(f"    Depth {depth}: {count:>4} {bar}")
    print()

    # Common path prefixes
    path_prefixes = Counter(
        url[len(base_url) :].split("/")[1] if "/" in url[len(base_url) :] else "" for url in urls
    )

    print("  Top URL Path Prefixes:")
    for prefix, count in path_prefixes.most_common(10):
        if prefix:
            print(f"    /{prefix:<20} {count:>6}")
    print()


def analyze_errors(data: dict[str, Any]) -> None:
    """Analyze errors encountered during crawl.

    :param data: Spider output data
    """
    errors = data.get("error_urls", {})
    if not errors:
        print("No errors encountered during crawl.")
        print()
        return

    print("Error Analysis:")
    print("-" * 70)
    print(f"  Total Errors: {len(errors)}")
    print()

    # Group by error type
    error_types: dict[str, list[str]] = {}
    for url, error_msg in errors.items():
        error_type = error_msg.split(":")[0]
        error_types.setdefault(error_type, []).append(url)

    print("  Errors by Type:")
    for error_type, urls_list in sorted(error_types.items()):
        print(f"    {error_type}: {len(urls_list)}")
        for url in urls_list[:3]:
            print(f"      - {url}")
        if len(urls_list) > 3:
            print(f"      ... and {len(urls_list) - 3} more")
    print()


def export_api_endpoints(data: dict[str, Any], output_path: Path) -> None:
    """Export unique API endpoints to a text file.

    :param data: Spider output data
    :param output_path: Path to write API endpoints
    """
    captures = data.get("network_captures", [])
    api_endpoints = sorted({c["url"] for c in captures if "/api/" in c["url"]})

    output_path.write_text("\n".join(api_endpoints) + "\n")
    print(f"Exported {len(api_endpoints)} API endpoints to: {output_path}")
    print()


def export_mutations(data: dict[str, Any], output_path: Path) -> None:
    """Export discovered mutations to a JSON file.

    :param data: Spider output data
    :param output_path: Path to write mutations JSON
    """
    mutations = data.get("discovered_mutations", [])
    output_path.write_text(json.dumps(mutations, indent=2, sort_keys=True))
    print(f"Exported {len(mutations)} mutations to: {output_path}")
    print()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for spider output analysis.

    :param argv: Command-line arguments (defaults to sys.argv[1:])
    :returns: Exit code (0 = success, non-zero = error)
    """
    parser = argparse.ArgumentParser(
        description="Analyze and summarize spider output JSON files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Spider output JSON file to analyze",
    )
    parser.add_argument(
        "--export-apis",
        type=Path,
        metavar="FILE",
        help="Export unique API endpoints to text file",
    )
    parser.add_argument(
        "--export-mutations",
        type=Path,
        metavar="FILE",
        help="Export discovered mutations to JSON file",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip summary output (useful with --export-* flags)",
    )

    args = parser.parse_args(argv)

    try:
        data = load_spider_output(args.input)

        if not args.no_summary:
            print_summary(data)
            analyze_mutations(data)
            analyze_network(data)
            analyze_urls(data)
            analyze_errors(data)

        if args.export_apis:
            export_api_endpoints(data, args.export_apis)

        if args.export_mutations:
            export_mutations(data, args.export_mutations)

        return 0

    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

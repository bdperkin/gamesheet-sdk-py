#!/usr/bin/env python3
# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Analyze and summarize spider output JSON files.

This utility provides quick analysis and insights from spider crawl results, including statistics, mutation
summaries, and API endpoint extraction.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


def load_spider_output(path: Path) -> dict[str, Any]:
    """Load and validate spider output JSON.

    :param path: Path to spider output JSON file
    :type path: Path
    :returns: Parsed spider output data
    :rtype: dict[str, Any]
    :raises FileNotFoundError: If spider output file does not exist
    :raises ValueError: If file is not valid JSON or missing required fields
    """
    if not path.exists():
        msg = f"Spider output not found: {path}"
        raise FileNotFoundError(msg)
    try:
        data: dict[str, Any] = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON in {path}: {exc}"
        raise ValueError(msg) from exc
    required_fields = ["season_id", "base_url", "summary", "visited_urls"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        missing_str = ", ".join(missing)
        msg = f"Missing required fields: {missing_str}"
        raise ValueError(msg)
    return data


def print_summary(data: dict[str, Any]) -> None:
    """Print overview summary statistics.

    :param data: Spider output data
    :type data: dict[str, Any]
    """
    print("=" * 70)
    season_id = data["season_id"]
    print(f"Spider Output Analysis - Season {season_id}")
    print("=" * 70)
    base_url = data["base_url"]
    print(f"Base URL: {base_url}")
    crawl_time = data.get("crawl_timestamp", "N/A")
    print(f"Crawl Time: {crawl_time}")
    print()
    print("Summary Statistics:")
    print("-" * 70)
    summary = data["summary"]
    visited = summary["visited_urls"]
    mutations = summary["discovered_mutations"]
    captures = summary["network_captures"]
    links = summary["external_links"]
    errors = summary["errors"]
    print(f"  Visited URLs:         {visited:>6}")
    print(f"  Discovered Mutations: {mutations:>6}")
    print(f"  Network Captures:     {captures:>6}")
    print(f"  External Links:       {links:>6}")
    print(f"  Errors:               {errors:>6}")
    print()


def analyze_mutations(data: dict[str, Any]) -> None:
    """Analyze and summarize discovered mutations.

    :param data: Spider output data
    :type data: dict[str, Any]
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
    :type data: dict[str, Any]
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
    :type data: dict[str, Any]
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
        bar_chart = "█" * (count * 40 // max(depths.values()))
        print(f"    Depth {depth}: {count:>4} {bar_chart}")
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
    :type data: dict[str, Any]
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
    :type data: dict[str, Any]
    :param output_path: Path to write API endpoints
    :type output_path: Path
    """
    captures = data.get("network_captures", [])
    api_endpoints = sorted({c["url"] for c in captures if "/api/" in c["url"]})
    output_path.write_text("\n".join(api_endpoints) + "\n")
    print(f"Exported {len(api_endpoints)} API endpoints to: {output_path}")
    print()


def export_mutations(data: dict[str, Any], output_path: Path) -> None:
    """Export discovered mutations to a JSON file.

    :param data: Spider output data
    :type data: dict[str, Any]
    :param output_path: Path to write mutations JSON
    :type output_path: Path
    """
    mutations = data.get("discovered_mutations", [])
    output_path.write_text(json.dumps(mutations, indent=2, sort_keys=True))
    print(f"Exported {len(mutations)} mutations to: {output_path}")
    print()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for spider output analysis.

    :param argv: Command-line arguments (defaults to sys.argv[1:])
    :type argv: list[str] | None
    :returns: Integer exit code.
    :rtype: int
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
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1
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


if __name__ == "__main__":
    sys.exit(main())

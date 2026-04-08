#!/usr/bin/env python3
"""Search npm for packages tagged with the Pi package keyword."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search npm for Pi packages using the 'pi-package' keyword."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Optional free-text query to combine with the pi-package keyword.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of matches to return (default: 10, max: 50).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of formatted text.",
    )
    return parser.parse_args()


def build_search_text(query: str) -> str:
    terms = ["keywords:pi-package"]
    if query.strip():
        terms.append(query.strip())
    return " ".join(terms)


def fetch_results(query: str, limit: int) -> list[dict[str, Any]]:
    text = build_search_text(query)
    url = (
        "https://registry.npmjs.org/-/v1/search"
        f"?text={quote(text)}&size={min(max(limit, 1), 50)}"
    )
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "pi-assistant-search/1.0",
        },
    )

    with urlopen(request, timeout=20) as response:
        payload = json.load(response)

    matches: list[dict[str, Any]] = []
    for item in payload.get("objects", []):
        package = item.get("package", {})
        keywords = [
            keyword.lower()
            for keyword in package.get("keywords", []) or []
            if isinstance(keyword, str)
        ]
        if "pi-package" not in keywords:
            continue

        links = package.get("links", {}) or {}
        matches.append(
            {
                "name": package.get("name", ""),
                "version": package.get("version", ""),
                "description": (package.get("description") or "").strip(),
                "date": package.get("date", ""),
                "keywords": package.get("keywords", []) or [],
                "npm": links.get("npm", ""),
                "homepage": links.get("homepage", ""),
                "repository": links.get("repository", ""),
            }
        )

    return matches


def print_human(matches: list[dict[str, Any]], query: str) -> None:
    if not matches:
        label = query.strip() or "all packages"
        print(f"No Pi packages found for query: {label}")
        return

    for index, package in enumerate(matches, start=1):
        print(f"{index}. {package['name']}@{package['version']}")
        if package["description"]:
            print(f"   {package['description']}")
        if package["date"]:
            print(f"   Published: {package['date']}")
        npm_url = package["npm"] or f"https://www.npmjs.com/package/{package['name']}"
        print(f"   npm: {npm_url}")
        if package["homepage"]:
            print(f"   homepage: {package['homepage']}")
        if package["repository"]:
            print(f"   repo: {package['repository']}")


def main() -> int:
    args = parse_args()

    try:
        matches = fetch_results(args.query, args.limit)
    except HTTPError as error:
        print(f"npm search request failed: HTTP {error.code}", file=sys.stderr)
        return 1
    except URLError as error:
        print(f"npm search request failed: {error.reason}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(matches, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print_human(matches, args.query)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

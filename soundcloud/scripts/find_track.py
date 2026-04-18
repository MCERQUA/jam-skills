#!/usr/bin/env python3
"""
Find a public SoundCloud track by free-text query.

Usage:
    python3 find_track.py "artist - track"
    python3 find_track.py "artist track remix" --json
    python3 find_track.py "stilo magolide bhare" --limit 5

Requires:
    SERPER_API_KEY environment variable
    python3 stdlib only (urllib, json, argparse)
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


SERPER_ENDPOINT = "https://google.serper.dev/search"
OEMBED_ENDPOINT = "https://soundcloud.com/oembed"

# Track URLs look like https://soundcloud.com/<user>/<slug>
# Exclude /sets/ (playlists), /stations/, /tags/, /discover etc.
TRACK_URL_RE = re.compile(
    r"^https?://(?:www\.|m\.)?soundcloud\.com/[^/\s]+/(?!sets/|stations/|tracks$)[^/\s?#]+/?(?:\?.*)?$",
    re.IGNORECASE,
)


def serper_search(query: str, num: int = 10) -> list[dict]:
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError("SERPER_API_KEY not set")

    body = json.dumps({"q": f'site:soundcloud.com {query}', "num": num}).encode()
    req = urllib.request.Request(
        SERPER_ENDPOINT,
        data=body,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data.get("organic", []) or []


def oembed_lookup(url: str) -> dict | None:
    params = urllib.parse.urlencode({"format": "json", "url": url})
    try:
        with urllib.request.urlopen(f"{OEMBED_ENDPOINT}?{params}", timeout=8) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None
        raise
    except urllib.error.URLError:
        return None


def find(query: str, limit: int) -> dict:
    results = serper_search(query, num=max(limit * 3, 10))
    candidates = []
    for r in results:
        url = (r.get("link") or "").strip()
        if TRACK_URL_RE.match(url):
            candidates.append(url)
        if len(candidates) >= limit:
            break

    if not candidates:
        return {"ok": False, "error": f"no soundcloud track found for {query!r}"}

    for url in candidates:
        data = oembed_lookup(url)
        if not data:
            continue
        return {
            "ok": True,
            "url": url,
            "title": data.get("title"),
            "author": data.get("author_name"),
            "author_url": data.get("author_url"),
            "artwork": data.get("thumbnail_url"),
            "embed_html": data.get("html"),
            "provider": "SoundCloud",
        }

    return {
        "ok": False,
        "error": f"candidates found but oEmbed blocked/failed for all ({len(candidates)} tried)",
        "candidates": candidates,
    }


def main():
    ap = argparse.ArgumentParser(description="Find a public SoundCloud track.")
    ap.add_argument("query", help="free-text search (artist - track)")
    ap.add_argument("--limit", type=int, default=3, help="max candidates to evaluate (default 3, max 10)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    limit = max(1, min(args.limit, 10))
    try:
        result = find(args.query, limit)
    except Exception as e:
        result = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if not result.get("ok"):
        print(f"not found: {result.get('error')}")
        return 1

    print(f"{result['title']}")
    print(f"  by {result.get('author') or 'unknown'}")
    print(f"  url: {result['url']}")
    if result.get("artwork"):
        print(f"  art: {result['artwork']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

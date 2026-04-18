#!/usr/bin/env python3
"""
Find a public Bandcamp track or album by free-text query.

Usage:
    python3 find_track.py "artist - album"
    python3 find_track.py "artist track" --kind track
    python3 find_track.py "stilo magolide" --json

Requires:
    SERPER_API_KEY environment variable
    python3 stdlib only
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


SERPER_ENDPOINT = "https://google.serper.dev/search"
USER_AGENT = "Mozilla/5.0 (JamBot bandcamp-skill/1.0)"

# Bandcamp URLs: <artist>.bandcamp.com/album/<slug> or /track/<slug>
BC_URL_RE = re.compile(
    r"^https?://([a-z0-9-]+)\.bandcamp\.com/(album|track)/([a-z0-9-]+)/?(?:\?.*)?$",
    re.IGNORECASE,
)

META_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\']([^"\']+)["\'][^>]*content=["\']([^"\']*)["\']',
    re.IGNORECASE,
)
BC_PROPS_RE = re.compile(
    r'<meta\s+name=["\']bc-page-properties["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def serper_search(query: str, num: int = 10) -> list[dict]:
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError("SERPER_API_KEY not set")

    body = json.dumps({"q": f'site:bandcamp.com {query}', "num": num}).encode()
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


def fetch_page(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read(1_500_000)  # cap at 1.5MB
            return raw.decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None


def parse_meta(page: str) -> dict:
    out = {}
    for k, v in META_RE.findall(page):
        out.setdefault(k.lower(), html.unescape(v))
    return out


def parse_bc_props(page: str) -> dict | None:
    m = BC_PROPS_RE.search(page)
    if not m:
        return None
    try:
        return json.loads(html.unescape(m.group(1)))
    except json.JSONDecodeError:
        return None


BC_KIND_MAP = {"a": "album", "t": "track", "album": "album", "track": "track"}


def build_embed(item_id: int, kind: str) -> tuple[str, str]:
    """Return (embed_url, embed_iframe_html) for a bandcamp item."""
    kind_key = BC_KIND_MAP.get(kind, "track")
    embed_url = (
        f"https://bandcamp.com/EmbeddedPlayer/{kind_key}={item_id}/"
        "size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/"
        "artwork=small/transparent=true/"
    )
    iframe = (
        f'<iframe style="border:0;width:100%;height:120px;" '
        f'src="{embed_url}" seamless></iframe>'
    )
    return embed_url, iframe


def classify_url(url: str) -> tuple[str | None, str | None]:
    """Return (kind, artist_slug) or (None, None)."""
    m = BC_URL_RE.match(url)
    if not m:
        return None, None
    artist, kind, _slug = m.group(1), m.group(2).lower(), m.group(3)
    return kind, artist


def find(query: str, kind_filter: str, limit: int) -> dict:
    results = serper_search(query, num=max(limit * 3, 10))
    candidates = []
    for r in results:
        url = (r.get("link") or "").strip()
        kind, _artist = classify_url(url)
        if not kind:
            continue
        if kind_filter != "any" and kind != kind_filter:
            continue
        candidates.append((url, kind))
        if len(candidates) >= limit:
            break

    if not candidates:
        return {"ok": False, "error": f"no bandcamp page found for {query!r}"}

    for url, kind in candidates:
        page = fetch_page(url)
        if not page:
            continue
        meta = parse_meta(page)
        props = parse_bc_props(page) or {}
        item_id = props.get("item_id")
        item_type = BC_KIND_MAP.get(props.get("item_type") or kind, kind)

        result = {
            "ok": True,
            "url": url,
            "kind": item_type,
            "title": meta.get("og:title"),
            "artist": meta.get("og:site_name") or meta.get("twitter:app:name:iphone"),
            "artwork": meta.get("og:image"),
            "description": meta.get("og:description"),
            "provider": "Bandcamp",
        }
        if item_id:
            embed_url, iframe = build_embed(int(item_id), item_type)
            result["embed_url"] = embed_url
            result["embed_html"] = iframe
        return result

    return {
        "ok": False,
        "error": f"candidates found but all page fetches failed ({len(candidates)} tried)",
        "candidates": [c[0] for c in candidates],
    }


def main():
    ap = argparse.ArgumentParser(description="Find a public Bandcamp track or album.")
    ap.add_argument("query", help="free-text search (artist - track/album)")
    ap.add_argument("--kind", choices=["track", "album", "any"], default="any")
    ap.add_argument("--limit", type=int, default=3, help="max candidates to evaluate (1-10)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    limit = max(1, min(args.limit, 10))
    try:
        result = find(args.query, args.kind, limit)
    except Exception as e:
        result = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if not result.get("ok"):
        print(f"not found: {result.get('error')}")
        return 1

    print(f"{result.get('title') or '(untitled)'}  [{result.get('kind')}]")
    print(f"  artist: {result.get('artist') or 'unknown'}")
    print(f"  url: {result['url']}")
    if result.get("embed_url"):
        print(f"  embed: {result['embed_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Resolve metadata for a known Bandcamp track/album URL.

Skips the search step — takes a URL directly, fetches the page, returns the
same JSON shape as find_track.py.

Usage:
    python3 resolve_url.py https://artist.bandcamp.com/album/name
"""

import json
import sys

# Re-use helpers from find_track.py (same directory)
sys.path.insert(0, "/mnt/shared-skills/bandcamp/scripts")
from find_track import (  # noqa: E402
    BC_URL_RE,
    BC_KIND_MAP,
    build_embed,
    classify_url,
    fetch_page,
    parse_bc_props,
    parse_meta,
)


def resolve(url: str) -> dict:
    kind, _artist = classify_url(url)
    if not kind:
        return {"ok": False, "error": "not a bandcamp track/album url"}

    page = fetch_page(url)
    if not page:
        return {"ok": False, "error": "page fetch failed"}

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: resolve_url.py <url>"}))
        sys.exit(1)
    try:
        print(json.dumps(resolve(sys.argv[1]), indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)

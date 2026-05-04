#!/usr/bin/env python3
"""
stitch-download-assets.py — Download remote assets referenced in a converted Stitch
project and rewrite the JSX <img src=> URLs to point at local public/images/<file>.

Reads <out>/.stitch-assets.json (produced by stitch-to-next.py) and downloads each
unique URL into <out>/public/images/stitch/<sha8>.<ext>. Then rewrites every page.tsx
to replace the remote URL with the local /images/stitch/<sha8>.<ext> path.

Usage:
  stitch-download-assets.py --project <next-project-root>
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def detect_ext(url: str, content_type: str | None) -> str:
    p = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".avif"):
        if p.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    if content_type:
        ct = content_type.lower()
        if "jpeg" in ct or "jpg" in ct:
            return ".jpg"
        if "png" in ct:
            return ".png"
        if "webp" in ct:
            return ".webp"
        if "svg" in ct:
            return ".svg"
        if "gif" in ct:
            return ".gif"
        if "avif" in ct:
            return ".avif"
    return ".jpg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="Next.js project root (must contain .stitch-assets.json)")
    args = ap.parse_args()

    root = Path(args.project).resolve()
    manifest_path = root / ".stitch-assets.json"
    if not manifest_path.exists():
        sys.exit(f"missing manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text())
    assets = manifest.get("assets", [])
    if not assets:
        print(json.dumps({"ok": True, "downloaded": 0, "rewrites": 0}))
        return

    images_dir = root / "public" / "images" / "stitch"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Dedup by URL (Stitch repeats some images across pages)
    by_url: dict[str, str] = {}  # url -> local path (e.g. /images/stitch/abc.jpg)
    download_count = 0
    fail_count = 0

    for asset in assets:
        url = asset["url"]
        if url in by_url:
            continue
        sha8 = hashlib.sha1(url.encode()).hexdigest()[:8]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                content_type = r.headers.get("Content-Type", "")
                data = r.read()
            ext = detect_ext(url, content_type)
            local_name = f"{sha8}{ext}"
            (images_dir / local_name).write_bytes(data)
            by_url[url] = f"/images/stitch/{local_name}"
            download_count += 1
        except Exception as e:
            sys.stderr.write(f"FAIL {url}: {e}\n")
            fail_count += 1

    # Rewrite every page.tsx to replace remote URLs with local paths.
    rewrites = 0
    pages = list((root / "src" / "app").rglob("page.tsx"))
    for page in pages:
        text = page.read_text()
        original = text
        for url, local in by_url.items():
            if url in text:
                text = text.replace(url, local)
        if text != original:
            page.write_text(text)
            rewrites += 1

    # Update manifest with local paths
    manifest["assets_local_map"] = by_url
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(json.dumps({
        "ok": True,
        "downloaded": download_count,
        "failed": fail_count,
        "unique_urls": len(by_url),
        "rewrites": rewrites,
    }, indent=2))


if __name__ == "__main__":
    main()

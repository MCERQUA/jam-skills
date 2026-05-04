#!/usr/bin/env python3
"""
stitch-content-layer.py — Replace Stitch placeholder text with real intake values
across every page.tsx in a converted Next.js project.

Reads:
  --intake <intake.json>      (the website-setup form serialization)
  --project <project-root>    (Next.js project after stitch-to-next.py + asset download)

Substitutions performed (intake-driven, not hardcoded):
  - phone numbers (any format) → intake.phone
  - email addresses → intake.email
  - street addresses (regex match) → intake.address
  - business name occurrences (Stitch-supplied placeholder name) → intake.businessName
  - hero image (if intake.heroImage supplied) → replaces 1st large hero <img>
  - gallery images (if intake.gallery supplied) → replaces matching slot count
  - social URLs (if supplied) → wires footer social links

Generic. No client-specific hardcoding.

Smoke:
  stitch-content-layer.py --intake .intake.json --project /tmp/stitch-test
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def download_to_public(url: str, project: Path, subdir: str = "intake") -> str | None:
    """Download a remote URL into public/images/<subdir>/<sha8>.<ext>.
    Returns the local /images/... path on success, None on failure."""
    if not url or not url.startswith(("http://", "https://")):
        return url  # already local or empty
    images_dir = project / "public" / "images" / subdir
    images_dir.mkdir(parents=True, exist_ok=True)
    sha8 = hashlib.sha1(url.encode()).hexdigest()[:8]
    parsed = urlparse(url).path.lower()
    ext = ".jpg"
    for cand in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".avif"):
        if parsed.endswith(cand):
            ext = ".jpg" if cand == ".jpeg" else cand
            break
    local_name = f"{sha8}{ext}"
    target = images_dir / local_name
    if target.exists():
        return f"/images/{subdir}/{local_name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        target.write_bytes(data)
        return f"/images/{subdir}/{local_name}"
    except Exception as e:
        sys.stderr.write(f"download failed {url}: {e}\n")
        return None


PHONE_RE = re.compile(r"""
    \(?\d{3}\)?            # (425) or 425
    [\s.\-]?
    \d{3}
    [\s.\-]?
    \d{4}
""", re.VERBOSE)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# US street address pattern: digit(s) + street name + suffix + optional city/state/zip.
ADDRESS_RE = re.compile(r"""
    \d+\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*    # number + street name
    \s+(?:Street|St|Ave|Avenue|Rd|Road|Blvd|Boulevard|Way|Dr|Drive|Lane|Ln|Place|Pl|Court|Ct|Terrace|Ter|N|S|E|W)
    \.?
    (?:[,\s]+[A-Z][A-Za-z]+)?     # optional city
    (?:[,\s]+[A-Z]{2})?            # optional state
    (?:\s+\d{5}(?:-\d{4})?)?       # optional zip
""", re.VERBOSE)

TEL_HREF_RE = re.compile(r'href="tel:[+\d\-\s()]+"')
MAILTO_HREF_RE = re.compile(r'href="mailto:[^"]+"')


def find_business_name_candidates(text: str, intake: dict) -> list[str]:
    """Find Stitch's placeholder business name. Stitch usually uses a common phrasing —
    we look for likely candidates so we can swap them."""
    candidates = []
    # Standard Stitch placeholders observed: "Modern Artisan", "Acme Co.", etc.
    for cand in [
        "Modern Artisan",
        "Acme Co.",
        "Acme",
        "Lorem Ipsum",
        "Your Business",
        "Your Company",
    ]:
        if cand in text:
            candidates.append(cand)
    return candidates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", required=True)
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    intake = json.loads(Path(args.intake).read_text())
    root = Path(args.project).resolve()

    biz_name = intake.get("businessName", "").strip()
    phone = intake.get("phone", "").strip()
    email = intake.get("email", "").strip()
    address = intake.get("address", "").strip()
    socials = intake.get("socials", {}) or {}

    # ── Download intake media to public/images/ so the site is self-contained ──
    # Without this, pages reference src.jam-bot.com/uploads/... which is a
    # cross-tenant external dependency.
    raw_hero = (intake.get("heroImage") or "").strip()
    raw_logo = (intake.get("logo") or "").strip()
    raw_gallery = intake.get("gallery", []) or []

    hero_image = download_to_public(raw_hero, root, "intake") if raw_hero else ""
    logo_local = download_to_public(raw_logo, root, "intake") if raw_logo else ""
    gallery = []
    for g in raw_gallery:
        url = g.get("url") if isinstance(g, dict) else g
        if not url:
            continue
        local = download_to_public(url, root, "intake") if url.startswith(("http://", "https://")) else url
        if local:
            entry = dict(g) if isinstance(g, dict) else {}
            entry["url"] = local
            gallery.append(entry)

    # Tel: href digits-only form
    tel_digits = re.sub(r"\D", "", phone)

    pages = sorted((root / "src" / "app").rglob("page.tsx"))
    if not pages:
        sys.exit(f"no page.tsx files in {root}/src/app")

    # First, scan all pages to find which placeholder strings exist (so we can replace
    # them with intake.businessName). We do this once across ALL pages since Stitch
    # likely uses the same placeholder name throughout.
    sample = pages[0].read_text() + ("\n".join(p.read_text() for p in pages[1:]) if len(pages) > 1 else "")
    name_candidates = find_business_name_candidates(sample, intake) if biz_name else []

    report = {"pages": []}
    for page in pages:
        text = page.read_text()
        original = text
        sub_count = {"phone": 0, "email": 0, "address": 0, "name": 0, "hero": 0, "gallery": 0, "social": 0, "logo": 0}

        # Phone: replace every match in body text + tel hrefs.
        if phone:
            new_text, n = PHONE_RE.subn(phone, text)
            sub_count["phone"] = n
            text = new_text
            if tel_digits:
                text, n2 = TEL_HREF_RE.subn(f'href="tel:{tel_digits}"', text)
                sub_count["phone"] += n2

        # Email: replace every match.
        if email:
            text, n = EMAIL_RE.subn(email, text)
            sub_count["email"] = n
            text, n2 = MAILTO_HREF_RE.subn(f'href="mailto:{email}"', text)
            sub_count["email"] += n2

        # Address: replace structured matches.
        if address:
            text, n = ADDRESS_RE.subn(address, text)
            sub_count["address"] = n

        # Business name placeholder swap.
        for cand in name_candidates:
            count = text.count(cand)
            if count:
                text = text.replace(cand, biz_name)
                sub_count["name"] += count

        # Hero image: replace the first /images/stitch/<hash>.<ext> reference inside a
        # very large/hero-context <img>. Heuristic: first <img> after "Hero" comment or
        # within first 2KB of body.
        if hero_image:
            m = re.search(r'src="(/images/stitch/[a-f0-9]+\.(?:jpg|png|webp|jpeg))"', text)
            if m:
                text = text[:m.start(1)] + hero_image + text[m.end(1):]
                sub_count["hero"] = 1

        # Logo: every <img> whose alt or surrounding context indicates "logo" gets the
        # local logo path. Stitch designs sometimes use a wordmark-only navbar, in which
        # case there's nothing to replace — that's fine.
        if logo_local:
            logo_pat = re.compile(
                r'<img\b([^>]*\b(?:alt|class|className)="[^"]*\blogo\b[^"]*"[^>]*)\bsrc="[^"]*"',
                re.IGNORECASE,
            )
            new_text, n = logo_pat.subn(
                lambda m: f'<img{m.group(1)}src="{logo_local}"',
                text,
            )
            if n:
                text = new_text
                sub_count["logo"] = n

        # Gallery images: replace remaining stitch images with gallery items in order.
        if gallery:
            stitch_imgs = list(re.finditer(r'src="(/images/stitch/[a-f0-9]+\.(?:jpg|png|webp|jpeg))"', text))
            # Skip the first if we already used it for hero
            start = 1 if hero_image else 0
            for i, m in enumerate(stitch_imgs[start:start + len(gallery)]):
                if i >= len(gallery):
                    break
                gallery_url = gallery[i].get("url") if isinstance(gallery[i], dict) else gallery[i]
                if gallery_url:
                    # Re-find m in current text (offsets may have shifted)
                    text = text.replace(m.group(0), f'src="{gallery_url}"', 1)
                    sub_count["gallery"] += 1

        # Social links — only if non-empty. Replace href="#" inside elements with a
        # social icon class (best-effort).
        social_map = {
            "facebook": ["facebook.com", "fb.com"],
            "instagram": ["instagram.com"],
            "youtube": ["youtube.com", "youtu.be"],
            "linkedin": ["linkedin.com"],
            "twitter": ["twitter.com", "x.com"],
            "yelp": ["yelp.com"],
            "tiktok": ["tiktok.com"],
            "nextdoor": ["nextdoor.com"],
        }
        for net, url in socials.items():
            url = (url or "").strip()
            if not url:
                continue
            # Find href= matching this network's domains and replace.
            for pat in social_map.get(net, []):
                hits = re.findall(rf'href="https?://[^"]*{re.escape(pat)}[^"]*"', text)
                for hit in hits:
                    text = text.replace(hit, f'href="{url}"', 1)
                    sub_count["social"] += 1

        if text != original:
            page.write_text(text)
        report["pages"].append({"path": str(page.relative_to(root)), **sub_count})

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

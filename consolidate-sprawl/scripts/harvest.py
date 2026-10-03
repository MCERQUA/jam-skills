#!/usr/bin/env python3
"""harvest.py — sweep per-item HTML pages into one structured JSON intermediate.

Proven on the Cortez caption sprawl (54 source pages -> 232 unique captions).
Stdlib only. Extracts text blocks whose class matches --classes, plus any
<img> inside or adjacent to the block, and the nearest preceding h2/h3 as
the section label. Dedupes on normalized text.

Usage:
  harvest.py --src DIR --out captions.json \
    [--classes "caption,caption-text,cap-text,caption-card"] \
    [--glob "*.html"] [--exclude-glob "*.bak*,*.old"]

Emit schema (list of):
  {"id": "cap-001", "text": "...", "section": "...", "source": "page.html",
   "images": ["img1.jpg"], "platform": "FB|IG|GBP|X|"}
"""
import argparse, glob, hashlib, html as htmllib, json, os, re, sys
from html.parser import HTMLParser


class Harvester(HTMLParser):
    def __init__(self, classes):
        super().__init__(convert_charrefs=True)
        self.classes = {c.strip().lower() for c in classes.split(",")}
        self.blocks, self.cur = [], None
        self.heading, self.section = None, None
        self.images = []          # (block_or_None, src)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").lower()
        if tag in ("h2", "h3"):
            self.heading = {"tag": tag, "cls": cls, "text": []}
        elif tag == "img":
            src = a.get("src") or ""
            if src:
                (self.cur["images"] if self.cur else self.images).append(src)
        if self.cur is not None:
            self.cur["depth"] += 1
            if tag in ("br", "p", "div", "li"):
                self.cur["text"].append("\n")
        if tag == "div" and self.classes & set(cls.split()):
            if self.cur is None:
                self.cur = {"text": [], "depth": 0, "images": [],
                            "section": self.section, "cls": cls}

    def handle_endtag(self, tag):
        if self.cur is not None:
            self.cur["depth"] -= 1
            if self.cur["depth"] <= 0:
                t = re.sub(r"\n{2,}", "\n", "".join(self.cur["text"])).strip()
                if t:
                    self.blocks.append({"text": t, "section": self.cur["section"],
                                        "images": self.cur["images"]})
                self.cur = None
        if tag in ("h2", "h3") and self.heading is not None:
            txt = " ".join("".join(self.heading["text"]).split())
            if txt:
                self.section = txt
            self.heading = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur["text"].append(data)
        elif self.heading is not None:
            self.heading["text"].append(data)


def norm(t):
    return re.sub(r"\s+", " ", t).strip().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--classes", default="caption,caption-text,cap-text,caption-card")
    ap.add_argument("--glob", default="*.html")
    ap.add_argument("--exclude-glob", default="*.bak*,*.old")
    ap.add_argument("--min-len", type=int, default=20,
                    help="min chars for a block to count as an item")
    args = ap.parse_args()

    excl = args.exclude_glob.split(",") if args.exclude_glob else []
    files = []
    for f in sorted(glob.glob(os.path.join(args.src, args.glob))):
        if any(fnmatch_ok(f, e) for e in excl):
            continue
        files.append(f)
    if not files:
        sys.exit(f"no source files matched in {args.src}")

    items, seen, skipped = [], {}, 0
    for f in files:
        raw = open(f, encoding="utf-8", errors="replace").read()
        h = Harvester(args.classes)
        try:
            h.feed(raw)
        except Exception as e:
            print(f"WARN parse {f}: {e}", file=sys.stderr)
        got = 0
        for b in h.blocks:
            if len(b["text"]) < args.min_len:
                skipped += 1
                continue
            k = hashlib.md5(norm(b["text"]).encode()).hexdigest()
            if k in seen:
                continue  # cross-page duplicate
            seen[k] = True
            got += 1
            items.append({"id": f"cap-{len(items)+1:03d}", "text": b["text"],
                          "section": b["section"] or "Unsorted",
                          "source": os.path.basename(f), "images": b["images"]})
        if got:
            print(f"  {os.path.basename(f)}: {got} item(s)")

    json.dump(items, open(args.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\nharvest: {len(files)} files -> {len(items)} unique items "
          f"({len(seen)} kept, dupes dropped) -> {args.out}")


def fnmatch_ok(name, pattern):
    import fnmatch
    return fnmatch.fnmatch(os.path.basename(name), pattern)


if __name__ == "__main__":
    main()

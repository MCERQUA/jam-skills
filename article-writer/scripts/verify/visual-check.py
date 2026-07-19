#!/usr/bin/env python3
"""Visual QA gate for article-writer Phase 8 — render the page like a reader and FAIL on:

  1. horizontal overflow (document scrollWidth > viewport) at any tested viewport
  2. broken images (naturalWidth == 0)
  3. `@media (prefers-color-scheme: dark)` blocks in article CSS — articles ship inside
     an always-light site shell; per-article dark overrides render dark-on-dark headings
     and grey-on-light cards on dark-mode phones (DSF incident 2026-07-19)

It also emits JPEG strips of the FULL page (light desktop + dark-scheme mobile) into
--out. THE REVIEWING AGENT MUST OPEN AND LOOK AT THE STRIPS — this script catches the
mechanical failures; only eyes catch "this looks bad" (muddy palette, light-grey-on-white,
cramped sections). Do not mark Phase 8 passed without viewing them.

Usage:
  visual-check.py --serve-dir <static site root> --path /blog/<slug>/ --out <dir>
  visual-check.py --html-file <standalone article html> --out <dir>

Exit 0 = mechanical checks passed (strips still need eyes). Exit 1 = hard failure.
Requires: playwright (chromium installed), Pillow.
"""
import argparse, json, os, re, sys, threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve-dir")
    ap.add_argument("--path", default="/")
    ap.add_argument("--html-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--viewports", default="390,1280")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright
    from PIL import Image

    os.makedirs(args.out, exist_ok=True)
    failures = []

    if args.html_file:
        serve_dir = str(Path(args.html_file).parent)
        path = "/" + Path(args.html_file).name
        css_src = open(args.html_file, encoding="utf-8", errors="replace").read()
    else:
        serve_dir, path = args.serve_dir, args.path
        css_src = None

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a): pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=serve_dir))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}{path}"

    widths = [int(w) for w in args.viewports.split(",")]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in widths:
            scheme = "dark" if width < 800 else "light"  # mobile tested in dark to catch scheme bugs
            ctx = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme)
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(1200)
            # scroll through the page so loading="lazy" images actually load,
            # otherwise below-fold images false-positive as broken
            page.evaluate("""async () => {
                const h = document.documentElement.scrollHeight;
                for (let y = 0; y <= h; y += 800) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
                window.scrollTo(0, 0);
                await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
            }""")
            page.wait_for_timeout(500)
            m = page.evaluate("""() => ({
                vw: document.documentElement.clientWidth,
                scrollW: document.documentElement.scrollWidth,
                brokenImgs: [...document.images].filter(i => i.complete && !i.naturalWidth).map(i => i.src).slice(0, 10),
                darkBlocks: [...document.querySelectorAll('style')]
                    .filter(s => /prefers-color-scheme\\s*:\\s*dark/.test(s.textContent)).length,
            })""")
            if m["scrollW"] > m["vw"] + 2:
                failures.append(f"[{width}px] horizontal overflow: scrollWidth {m['scrollW']} > viewport {m['vw']}")
            if m["brokenImgs"]:
                failures.append(f"[{width}px] broken images: {m['brokenImgs']}")
            if m["darkBlocks"]:
                failures.append(f"[{width}px] {m['darkBlocks']} prefers-color-scheme:dark style block(s) — remove them")
            tag = f"{width}px-{scheme}"
            full = os.path.join(args.out, f"full-{tag}.png")
            page.screenshot(path=full, full_page=True)
            im = Image.open(full)
            w, h = im.size
            strip_h, n = 1800, min((h + 1799) // 1800, 10)
            for i in range(n):
                s = im.crop((0, i * strip_h, w, min((i + 1) * strip_h, h)))
                if s.width > 800:
                    s = s.resize((800, int(s.height * 800 / s.width)))
                s.convert("RGB").save(os.path.join(args.out, f"strip-{tag}-{i:02d}.jpg"), quality=68)
            os.remove(full)
            print(f"[{tag}] {w}x{h}, {n} strips -> {args.out}")
            ctx.close()
        browser.close()
    srv.shutdown()

    if css_src and re.search(r"prefers-color-scheme\s*:\s*dark", css_src):
        failures.append("source HTML contains a prefers-color-scheme:dark block — remove it")

    report = {"url": url, "failures": failures}
    with open(os.path.join(args.out, "visual-check.json"), "w") as f:
        json.dump(report, f, indent=2)
    if failures:
        print("VISUAL CHECK FAILED:")
        for x in failures:
            print("  -", x)
        sys.exit(1)
    print("Mechanical checks passed. NOW OPEN THE STRIPS AND LOOK AT THEM before passing Phase 8.")

main()

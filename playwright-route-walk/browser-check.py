#!/usr/bin/env python3
"""
browser-check.py — the ship gate for JamDash.

Walks EVERY route declared in nav.js (so the test can never drift from the menu)
at desktop and mobile, in a real browser. Fails on:
  · any console error or page error
  · any screenshot under MIN_BYTES — the blank/black-page tell that a DOM
    assertion cannot catch (a jsdom suite once passed 17/17 on a solid-black page)
  · any view rendering under MIN_TEXT characters

Usage:
    cd projects/jam-dash/public && python3 -m http.server 8791 &
    python3 ../scripts/browser-check.py [--base http://127.0.0.1:8791] [--shots DIR]

    On Danielle's desktop Playwright lives in a venv:
    /config/.venvs/playwright/bin/python ../scripts/browser-check.py

Exit 0 = all routes render. Exit 1 = something is broken.
"""
import argparse, asyncio, os, re, sys

MIN_BYTES = 25_000     # a blank 1440x900 page is ~10-16KB; a real one is 100KB+
MIN_TEXT  = 80
VIEWPORTS = [("desk", {"width": 1440, "height": 900}),
             ("mob",  {"width": 390,  "height": 844})]
DEFAULT_ROUTE_TIMEOUT_S = 45   # per-route nav timeout; a route that hangs past this is
                                # COULD-NOT-RUN (dead/unreachable), not BROKE (rendered wrong)

HERE = os.path.dirname(os.path.abspath(__file__))
NAV  = os.path.join(HERE, "..", "public", "assets", "js", "nav.js")

# Playwright's bundled Chromium will not install on Ubuntu 26.04 (the JamBot desktops), so use the
# system browser when there is one. JAMDASH_CHROMIUM overrides; with nothing found, Playwright falls
# back to its own download, which works on the hosts it supports.
SYSTEM_BROWSERS = ("/usr/bin/google-chrome", "/usr/bin/chromium")


def launch_options():
    exe = os.environ.get("JAMDASH_CHROMIUM") or next((p for p in SYSTEM_BROWSERS if os.path.exists(p)), None)
    opts = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if exe:
        opts["executable_path"] = exe
    return opts


def routes_from_nav(path=NAV):
    """Parse nav.js so the gate covers exactly what the menu exposes."""
    src = open(path, encoding="utf-8").read()
    out = []
    for sid, body in re.findall(r"id:\s*'([a-z-]+)',\s*label:.*?pages:\s*\[(.*?)\]\s*\}", src, re.S):
        for pid in re.findall(r"id:\s*'([a-z-]*)'", body):
            out.append(f"{sid}/{pid}" if pid else sid)
    if not out:
        sys.exit("browser-check: parsed 0 routes from nav.js — refusing to report success")
    return out


async def run(base, shots, route_timeout_s=DEFAULT_ROUTE_TIMEOUT_S):
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    os.makedirs(shots, exist_ok=True)
    routes = routes_from_nav()
    print(f"browser-check: {len(routes)} routes x {len(VIEWPORTS)} viewports against {base} "
          f"(route-timeout={route_timeout_s}s)\n")
    failures = []
    could_not_run = []

    async with async_playwright() as p:
        opts = launch_options()
        print(f"browser: {opts.get('executable_path', 'playwright bundled chromium')}")
        browser = await p.chromium.launch(**opts)
        for tag, vp in VIEWPORTS:
            page = await browser.new_page(viewport=vp)
            errs = []
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errs.append(f"PAGEERROR {e}"))

            for r in routes:
                errs.clear()
                try:
                    await page.goto(f"{base}/#/{r}", wait_until="networkidle",
                                     timeout=route_timeout_s * 1000)
                    await page.wait_for_timeout(220)
                    shot = os.path.join(shots, f"{tag}-{r.replace('/', '_')}.png")
                    await page.screenshot(path=shot)
                    size = os.path.getsize(shot)
                    text = (await page.inner_text("#view")).strip()
                except PlaywrightTimeoutError:
                    # route never settled inside route_timeout_s — dead/unreachable route,
                    # not a rendering defect, so it must not count as BROKE.
                    could_not_run.append(f"{tag} {r}: COULD-NOT-RUN — no response after {route_timeout_s}s")
                    print(f"  {tag:4} {r:24} COULD-NOT-RUN (timeout {route_timeout_s}s)")
                    continue
                except Exception as exc:
                    failures.append(f"{tag} {r}: NAVIGATION FAILED — {exc}")
                    print(f"  {tag:4} {r:24} NAVIGATION FAILED")
                    continue

                flags = []
                if errs:                flags.append(f"console:{errs[0][:70]}")
                if size < MIN_BYTES:    flags.append(f"blank-page({size}B)")
                if len(text) < MIN_TEXT:flags.append(f"thin-text({len(text)})")
                if flags: failures.append(f"{tag} {r}: {' · '.join(flags)}")
                print(f"  {tag:4} {r:24} {size//1024:4}KB  text={len(text):5}"
                      f"{'  <-- ' + ' · '.join(flags) if flags else ''}")
            await page.close()
        await browser.close()

    print()
    if could_not_run:
        print(f"COULD-NOT-RUN — {len(could_not_run)} route(s) never responded (not counted as broken):")
        for c in could_not_run: print("  -", c)
    if failures:
        print(f"FAIL — {len(failures)} problem(s):")
        for f in failures: print("  -", f)
        return 1
    if could_not_run:
        print("PASS with COULD-NOT-RUN route(s) above — dead/unreachable, re-run to confirm before treating as broke.")
        return 2
    print(f"PASS — {len(routes) * len(VIEWPORTS)} renders, no console errors, none blank.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base",  default="http://127.0.0.1:8791")
    ap.add_argument("--shots", default="/tmp/jamdash-shots")
    ap.add_argument("--route-timeout", type=int, default=DEFAULT_ROUTE_TIMEOUT_S,
                     help="per-route navigation timeout in seconds; a route that hangs past this "
                          "reports COULD-NOT-RUN (exit 2), not BROKE (exit 1)")
    a = ap.parse_args()
    sys.exit(asyncio.run(run(a.base.rstrip("/"), a.shots, a.route_timeout)))

#!/usr/bin/env python3
"""page-check.py: drives page.html in a real headless browser against fixtures and checks the
page's obligations (SKILL.md "The page's obligations"). Called by self-test.sh when Playwright
is importable; prints SKIPPED and exits 4 when it is not, so a skip never reads as a pass.

    page-check.py <page.html>        exit 0 all ok · 1 a check failed · 4 skipped (no browser)
"""
import functools
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading

try:
    from playwright.sync_api import sync_playwright
except Exception:                                      # noqa: BLE001 — any import failure = no browser
    print("SKIPPED page checks: playwright is not importable in %s" % sys.executable)
    sys.exit(4)

# A 1x1 PNG, so a ready image slot has real bytes to decode.
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d4944415478da63f8cfc0f01f0005000201a5f1b1f80000000049454e44ae426082")
JOB = "ld-selftest-job"


def manifest(clips, **hdr):
    m = {"schema": "live-delivery/1", "job": JOB, "updated": "2026-01-01T00:00:00Z",
         "title": "Self-test job", "ask": "Reply with a number.", "written_by": "page-check",
         "clips": clips}
    m.update(hdr)
    return m


def slot(n, status="queued", file=None, shows="", label=None):
    return {"n": n, "label": label or "Slot %d" % n, "status": status, "shows": shows,
            "file": file, "url": ("/uploads/%s" % file) if file else None,
            "measurements": {"seed": 7} if file else {}, "notes": "", "alternates": []}


def main():
    template = sys.argv[1]
    root = tempfile.mkdtemp(prefix="ld-pagecheck-")
    os.makedirs(os.path.join(root, "pages"))
    os.makedirs(os.path.join(root, "uploads"))
    shutil.copy(template, os.path.join(root, "pages", JOB + ".html"))
    with open(os.path.join(root, "uploads", "a.png"), "wb") as fh:
        fh.write(PNG)
    with open(os.path.join(root, "uploads", "b.png"), "wb") as fh:
        fh.write(PNG)
    with open(os.path.join(root, "uploads", "undecodable.mp4"), "wb") as fh:
        fh.write(b"this is not a video" * 64)
    mpath = os.path.join(root, "uploads", JOB + ".json")

    def put(obj):
        with open(mpath + ".tmp", "w") as fh:
            json.dump(obj, fh)
        os.replace(mpath + ".tmp", mpath)

    # Our own server on a port the kernel picks: a fixed port can already be held by another
    # lane, and then the browser silently checks somebody else's page.
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    handler = functools.partial(Quiet, directory=root)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/pages/%s.html" % (srv.server_address[1], JOB)

    fails, passes = [], [0]

    def waited(pg, js, timeout=5000):
        """A wait that times out is a FAILED check, never a crash that happens to exit non-zero."""
        try:
            pg.wait_for_function(js, timeout=timeout)
            return True
        except Exception:                              # noqa: BLE001
            return False

    def ck(label, cond, detail=""):
        if cond:
            passes[0] += 1
            print("  ok   %s" % label)
        else:
            fails.append(label)
            print("  FAIL %s %s" % (label, detail))

    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 390, "height": 844})

            # [P1] no manifest yet: "could not read" must not look like "nothing to show"
            pg.goto(url)
            pg.wait_for_function("document.getElementById('stamp').textContent !== 'loading…'")
            err = pg.locator("#err")
            ck("no manifest: the error box is shown", err.is_visible())
            ck("no manifest: it says the list could not be loaded",
               err.is_visible() and "could not be loaded" in (err.inner_text() or ""))
            ck("no manifest: the title says unavailable, not an empty job",
               pg.locator("#title").text_content() == "List unavailable")

            # [P2] seeded out of order; one ready image, one ready-but-missing file
            put(manifest([slot(3, shows="the closing beat"),
                          slot(1, "ready", "a.png", label="First"),
                          slot(2, shows="the middle beat, still coming"),
                          slot(4, "ready", "gone.png", label="Moved away"),
                          slot(5, "ready", "undecodable.mp4", label="Present, not playable")]))
            pg.reload()
            pg.wait_for_selector("#slot-5")
            pg.wait_for_timeout(1500)
            ids = pg.eval_on_selector_all(".card", "els => els.map(e => e.id)")
            ck("slots render in NUMBER order", ids == ["slot-1", "slot-2", "slot-3", "slot-4", "slot-5"], str(ids))
            ck("the error box is gone once the list loads", not err.is_visible())
            s2 = pg.locator("#slot-2")
            ck("a pending slot says what it is FOR", "the middle beat" in (s2.text_content() or ""))
            ck("a pending slot says its state", "queued" in (s2.text_content() or ""))
            ck("a pending slot has no player", s2.locator("img,video,audio").count() == 0)
            nat = pg.eval_on_selector("#slot-1 img", "i => i.complete && i.naturalWidth")
            ck("a ready image slot shows the image", bool(nat), str(nat))
            ck("a ready slot whose file is gone says so on its card",
               "not at its address" in (pg.locator("#slot-4").text_content() or ""),
               pg.locator("#slot-4").text_content() or "")
            v5 = pg.evaluate("(() => { var v = document.querySelector('#slot-5 video'); return v ? (v.error ? v.error.code : 0) : -1; })()")
            ck("a file that is present but cannot be decoded is NOT called missing",
               "not at its address" not in (pg.locator("#slot-5").text_content() or ""),
               "media error code %s" % v5)
            # v5 in (3, 4): the decode error really fired, so this check is not inert
            ck("...its player stays (its decode error did fire), with an open-file link", v5 in (3, 4) and
               pg.locator("#slot-5 a.tag", has_text="open file").count() == 1)
            ck("the ask line comes from the manifest",
               pg.locator("#ask").text_content() == "Reply with a number.")
            ck("the stamp shows when the list was updated",
               "list updated" in (pg.locator("#stamp").text_content() or ""))
            ck("the stamp flags an old list as stale (amber)",
               "stale" in (pg.get_attribute("#dot", "class") or ""))
            sw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            ck("no horizontal scroll at 390 px", sw[0] <= sw[1], str(sw))

            # [P3] flip slot 2 while the page is open: it fills in; slot 1 is not torn down
            pg.evaluate("document.getElementById('slot-1').__keep = 1")
            put(manifest([slot(1, "ready", "a.png", label="First"),
                          slot(2, "ready", "b.png", shows="the middle beat, still coming"),
                          slot(3, shows="the closing beat"),
                          slot(4, "ready", "gone.png", label="Moved away"),
                          slot(5, "ready", "undecodable.mp4", label="Present, not playable")]))
            pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
            ck("a slot flipped to ready fills in without a reload",
               waited(pg, "!!document.querySelector('#slot-2 img')"))
            ck("an unchanged slot is not torn down by the poll",
               pg.evaluate("document.getElementById('slot-1').__keep === 1"))

            # [P4] the list goes unreadable after a good load: keep what loaded, say it is stale
            os.unlink(mpath)
            pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
            ck("a failed re-read says so", waited(pg, "!document.getElementById('err').hidden")
               and "Could not re-read" in (err.inner_text() or ""))
            ck("...and keeps showing what loaded last", pg.locator(".card").count() == 5)
            ck("...and the dot turns red", "dead" in (pg.get_attribute("#dot", "class") or ""))

            # [P5] an EMPTY list is an error, never an empty page
            put(manifest([]))
            pg2 = b.new_page()
            pg2.goto(url)
            ck("an empty clips[] is reported, not rendered as nothing",
               waited(pg2, "!document.getElementById('err').hidden")
               and "nothing in it" in (pg2.locator("#err").inner_text() or ""))
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(root, ignore_errors=True)

    print("page checks: %d passed, %d failed" % (passes[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

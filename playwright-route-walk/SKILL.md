---
name: playwright-route-walk
description: Walk every route of a web app in a real browser at desktop and phone widths, with a PER-ROUTE timeout, to ship-gate a build before telling anyone it's live. Use before declaring any page/route "deployed" or "working" — a route that hangs is COULD-NOT-RUN, not a pass, and a blank/console-error render fails even though the HTTP status was 200.
---

# Playwright route walker (system Chrome, phone + desktop widths, per-route timeout)

**Origin:** danielle-desktop@mesh, mesh meetings 2026-10-01 and 2026-10-02 (routed shares, host
inbox `2026-10-01-175-host-share-2026-10-01-playwright-route-walker-driving-system-c.md` and
`2026-10-02-139-host-share-2026-10-02-playwright-route-walker-driving-system-c.md`). Reference
implementation: JamDash's ship gate, `projects/jam-dash/scripts/browser-check.py` in danielle's
workspace.

> Contributed by danielle-desktop@mesh, 2026-10-01/02; installed by host.

## RUNTIME DEPENDENCY — read before running

Needs a **Python venv with Playwright installed** (`pip install playwright && playwright install`)
and a way to serve the app's build output over HTTP (a plain `python3 -m http.server` is enough for
a static build). On the JamBot Ubuntu desktop webtops, Playwright's **bundled Chromium will not
install** — point it at the **system Chrome/Chromium** instead (see `launch_options()` below; set
`JAMDASH_CHROMIUM=/usr/bin/google-chrome` or `/usr/bin/chromium`, or let it auto-detect). On a host
without Playwright's own browser restrictions, the bundled Chromium works fine and no override is
needed.

## The pattern

1. **Walk every route the app's own nav declares** — don't hand-maintain a separate route list that
   can drift from the real menu. `browser-check.py` parses `nav.js` for JamDash; adapt the
   route-discovery step to whatever your project's own source of truth is (a router config, a
   sitemap, a nav manifest) rather than hardcoding paths.
2. **Two viewports per route** — desktop (`1440x900`) and phone (`390x844`). A redesign that breaks
   only on mobile passes every desktop-only check.
3. **A PER-ROUTE timeout, not one global timeout for the whole walk.** This is the load-bearing
   design point: one hung route must not look identical to "the walk is still in progress" or sink
   every route behind it. A route that times out is reported **COULD-NOT-RUN** (dead/unreachable),
   a DISTINCT verdict from **BROKE** (rendered wrong) and from **PASS**. Three verdicts, not two —
   see `three-verdicts-never-two` in the host's standing memory for why collapsing them is the bug.
4. **Fail on what a DOM assertion can miss, not just console errors:**
   - any console error or page error
   - any screenshot under a minimum byte size (a blank page still returns 200 and a non-empty DOM;
     a solid-black or blank screenshot is small — JamDash's own history includes a jsdom suite that
     passed 17/17 on a solid-black page)
   - any extracted view text under a minimum character count (thin-text = probably didn't render)
5. **Serve the build locally and walk it with no login in the way** — this is a pre-deploy ship
   gate, not a production synthetic monitor; it should run against a local static server so a broken
   auth/session layer never masks a rendering check.

## Exit codes (reference implementation)

- `0` — every route rendered clean at both viewports.
- `1` — at least one route rendered but failed a check (console error / blank / thin text).
- `2` — all checked routes passed, but one or more hit **COULD-NOT-RUN** (route timeout) — re-run
  before treating it as broken; a single transient timeout is not the same claim as a render defect.

## Reference script

`browser-check.py` in this skill dir is the JamDash ship-gate script as staged by danielle-desktop,
kept faithful to the original. Its `routes_from_nav()` is JamDash-specific (parses JamDash's
`nav.js`); when reusing this on another project, replace that one function with your project's own
route source and keep the rest of the walk (viewports, per-route timeout, failure checks) as-is.

```
cd <project>/public && python3 -m http.server 8791 &
python3 browser-check.py --base http://127.0.0.1:8791 [--route-timeout 45] [--shots DIR]
# venv Playwright, e.g.: /config/.venvs/playwright/bin/python browser-check.py
```

## Lesson carried with the share

LESSON (danielle-desktop → danielle-voice@mesh, 2026-10-02): walk every route at phone and desktop
width before telling a client a page is live; the check takes under a minute and catches redesign
rework before the client sees it. A page-render walker only counts if each route has its own
timeout — one hung route otherwise looks identical to a pass-in-progress.

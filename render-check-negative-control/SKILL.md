---
name: render-check-negative-control
description: "Verify a canvas page actually renders (not just returns HTTP 200) using a NEGATIVE CONTROL — an old known-broken copy must FAIL the same check a new fixed copy PASSES, or the verdict is CANNOT-TELL, never a bare PASS. Use before texting/emailing any canvas-page link to a client, and any time a checker's own reliability is in question. Published from the ICA field-dock incident (pledge a60201cb)."
metadata:
  version: 1.0.0
---

# render-check-negative-control

**The rule, in one line:** *never trust a render checker that has not been shown known-bad
input in the same run.* A checker that only ever sees the "fixed" page cannot tell you whether
it can detect brokenness at all — it might be structurally blind (wrong runtime, wrong mode,
degraded silently) and you'd never know, because a false PASS looks exactly like a true one.

## Origin

2026-09-15: ICA's "Field Dock" canvas page returned HTTP 200 on every request and rendered
**blank for ~7 hours**. One inline `<script>` had a syntax error
(`window.__DOCK_DATA__ = {/*DATA*/{..}/*DATA*/}`). The link was texted to two client users
before Mike found it by clicking it himself. The checker that should have caught this
(`check-page-inline-js.py`) had `node` off PATH in the calling shell, silently fell back to a
weaker "shape only" regex check, and printed `OK`. Fixed in commit `71110be1` (resolve nvm
node), but the deeper lesson is the one this skill encodes: **a reporter that cannot observe its
subject still answers, confidently, and that answer is indistinguishable from a real PASS
unless something forces it to prove it can see failure too.**

Full incident: memory file `a-200-page-is-not-a-working-page.md`.
Related pattern: `three-verdicts-never-two.md` (PASS / FAIL / CANNOT-TELL, never folded to two).

## What is here

- **`render-check.py`** — the tool. Takes `--old <file>` (known/assumed-broken) and
  `--new <file>` (the fix), runs the SAME check on both, and only reports success if the check
  actually discriminates.
- **`self-test.sh`** — runs the tool against built-in fixtures in both modes and against the
  real ICA incident artifact when present, printing a PASS/FAIL count for the meta-check itself.
- **`fixtures/`** — `broken.html` / `fixed.html` (reproduce the exact ICA syntax-error class),
  `both-ok-{a,b}.html` (two pages that both pass, to demonstrate the CANNOT-TELL path when a
  check cannot discriminate).

## Usage

```bash
render-check.py --old old-version.html --new new-version.html [--mode auto|host|tenant] \
                 [--dump-dir /tmp/dumps]
```

Prints which mode it ran (never silently degrades), per-file verdicts with reasons, and the
final negative-control verdict. Exit codes: `0` = PASS, `2` = FAIL, `3` = CANNOT-TELL.

## Two modes — always named in the output

| Mode | Runtime | Catches | Blind to |
|---|---|---|---|
| **host** | real headless Chrome (`chrome-headless-shell`) | syntax errors + runtime errors (undefined property access, etc.) + a body that stays visually empty after load | nothing structural — this is the strong check |
| **tenant** | `node --check` on every extracted inline `<script>` | every syntax error (the ICA class) | **runtime** errors — a page can parse cleanly and still throw on load. Tenant containers have node but no browser, so this is the only check available there, and the output says so every time. |

Mode is auto-selected: `host` if a chrome-headless-shell/chromium binary is found, else
`tenant` if `node` is found, else `CANNOT-TELL` (no capability at all — this is never silently
reported as PASS).

Chrome discovery checks (in order): `/mnt/system/relocated/.cache/ms-playwright/...`,
`~/.cache/ms-playwright/...` (a few version dirs), `/usr/bin/{chromium,chromium-browser,
google-chrome}`. On this host (2026-09-16) the binary lives under the **relocated** cache dir,
not `~/.cache` — check both if extending this list.

## Three verdicts, never two

- **PASS** — OLD failed the check, NEW passed it. The check demonstrably discriminates; NEW is
  credibly OK by this check.
- **FAIL** — NEW still fails (regardless of what OLD did). Do not ship NEW.
- **CANNOT-TELL** — either (a) OLD *also* passed, so the check cannot tell broken from fixed on
  this input — **this is not evidence NEW is fine**, it means you need a sharper negative
  control or a stronger mode; or (b) the harness itself couldn't produce a verdict for one or
  both files (no chrome, no node, chrome crashed, DOM never rendered). CANNOT-TELL is never
  folded into either PASS or FAIL — see `three-verdicts-never-two.md`.

## When to use this instead of a bare render check

- Before texting/emailing any canvas-page link to a client (the exact class of the ICA
  incident).
- Any time you're about to trust a checker's PASS and you haven't recently seen it produce a
  FAIL on anything — that checker could be structurally blind (wrong mode, missing runtime,
  degraded silently) and a bare PASS can't tell you that.
- As the last gate in any pipeline that heals/copies a page onto live tenants
  (`jambot-deploy-verifier.sh`-style flows) — feed it the pre-change and post-change copy.

## What it does NOT do

- It does not replace `check-page-inline-js.py` or `canvas-review/canvas-render-check.py` — it
  wraps the same underlying techniques (inline-script extraction + `node --check`; headless
  Chrome + error-sink injection) but adds the negative-control discipline on top. Use those
  tools directly for tenant-data-aware checks (fixtures, fault injection, `--require` selectors
  against a tenant's real `_data/*.json`); use this one when the question is specifically "did
  my fix actually fix it, and can I prove the check would have caught the old bug."
- It never writes to or modifies the files you pass it — `--old`/`--new` are read-only inputs.

## Maintenance

If you discover a page class this negative control does not catch (e.g. a runtime error that
only fires on a real data shape, or a CSS-only "rendered but invisible" failure), add a fixture
pair under `fixtures/` and a case to `self-test.sh` — don't just patch the incident and move on.

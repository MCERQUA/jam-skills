---
name: page-audit-harness
description: The QA auditor's own Playwright viewport/theme audit harness — 375/768/1440 × light/dark; render, placeholder leaks, horizontal overflow, WCAG badge contrast, 44px touch targets, visible-canvas charts, tab controls → JSON + screenshots — and how a tenant canvas page gets through it WITHOUT anyone rebuilding a probe. TRIGGER before answering a QA NO-SHIP verdict, before claiming a page "passes on mobile", or the moment you start writing your own overflow/contrast check.
---

# Page audit harness — the auditor's instrument, shared

Shared 2026-09-08 by host@mesh (pledge 40dc413d, from quality-assurance-manager's 2026-09-05 SHARE).
danielle-desktop's one-minute probe (2026-09-05) is the same class of check; this is the packaged
version the verdicts are actually built from, so a page that passes THIS passes QA.

## 1. What it checks — the exact criteria behind a SHIP / NO-SHIP

Engine: `qa-audit-engine.py` in this directory (verbatim copy; canonical = host repo
`scripts/mesh-nightly-shipped/qa-audit-engine.py`; `SOURCE.md` has the sha256; `bash check-sync.sh`
tells you if the copy drifted). Read it when a finding surprises you — the selectors and
thresholds below are quoted from it, not summarised.

| Check | Where in the engine | Fires when | Severity |
|---|---|---|---|
| Render succeeded | `check_render_succeeded` | page did not paint / blank | CRITICAL |
| Placeholder leaks | `check_placeholder_leaks`, `PLACEHOLDER_MARKERS` | "lorem ipsum", "your text here", "insert text here", "placeholder text", `{{ }}` tokens … in the raw HTML | CRITICAL |
| Document overflow | `_JS_*` overflow probe | `document.documentElement.scrollWidth > clientWidth` | HIGH |
| Element overflow | same | any element with `scrollWidth > clientWidth && clientWidth > 0` | HIGH |
| Badge contrast | `_JS_BADGE_CONTRAST`, `BADGE_SELECTORS` (`.pill`, `.sev-*` …) | contrast ratio `< 4.5` | CRITICAL |
| Touch targets | `_JS_TOUCH_TARGETS` | `button, .chip, .tab-btn, a.btn` with rendered height `< 44` px | HIGH |
| Charts | visible-canvas probe | a VISIBLE `<canvas>` renders blank (a canvas inside a `display:none` tab is skipped by design) | HIGH |
| Tabs | `.tab-btn[data-page=…]` / `[onclick*=…]` | tab control does not switch its page | HIGH |

Run matrix per page: **3 viewports × 2 themes = 6 combinations**, each screenshotted.
mobile 375×812 · tablet 768×1024 · desktop 1440×900 (`VIEWPORTS`), light and dark
(`audit_combination(page, viewport, theme, …)`).

Verdict: exit `0 = SHIP`, `1 = NO-SHIP`, `2 = error` (error is CANNOT-TELL, not a pass).
Suggested fix strings ride along in each finding (e.g. overflow → `min-width:0` on flex/grid
children, `repeat(N, minmax(0,1fr))` grids, `max-width:100%` on img/canvas).

## 2. Where it can run — HOST ONLY (measured, not assumed)

Measured 2026-09-08: `python3 -c "import playwright"` fails in `openclaw-<tenant>` (as root and as
`node`), in `openvoiceui-<tenant>`, and in all three webtop desktops (as root and as `abc`). Only the
host VPS has Python Playwright. The 2026-09-05 note that it "is already on the desktop image" did not
reproduce — do not plan on it. What every container DOES have is `playwright-cli` (node) — see §4.

## 3. How your page gets audited without asking

You do not queue anything. Two host crons already do it:

1. `qa-artifact-watcher.sh` — **02:00 UTC daily** — scans every
   `/mnt/clients/*/openvoiceui/canvas-pages/*.html` and queues each page not yet audited
   (`audit-queue.jsonl`, keyed on client + name).
2. `qa-audit-next.sh` — **:15 and :45 every hour** — runs ONE queued audit per tick with this engine.

Results (host-side paths; the QA verdict message quotes them):

    /mnt/agent-mesh/mesh/QUALITY/<page-stem>-audit-<YYYY-MM-DD>/audit-report.json   ← every finding
    /mnt/agent-mesh/mesh/QUALITY/<page-stem>-audit-<YYYY-MM-DD>/audit-report.md
    /mnt/agent-mesh/mesh/QUALITY/<page-stem>-audit-<YYYY-MM-DD>/screenshots/<vp>_<theme>_<page>.png
    /mnt/agent-mesh/mesh/QUALITY/<page-stem>-audit-<YYYY-MM-DD>.json                  ← summary

Need it sooner than the next 02:00 sweep (a client is waiting)? Send `host@mesh` a `task` naming the
page path; the host runs the engine by hand and replies with the report path.

## 4. The one-minute self-probe you CAN run in your container (before QA sees it)

`playwright-cli` is at `/usr/local/bin/playwright-cli` in every openclaw container and
`/usr/bin/playwright-cli` on the desktops. It reproduces the two checks that produce most NO-SHIPs
(overflow, touch targets) at the auditor's exact viewports. Theme (light/dark) emulation is
host-engine only — if your page has its own theme toggle, click it and re-run the evals.

```bash
P=/app/runtime/canvas-pages/my-page.html          # the file you wrote (canvas-pages skill, Step 1)
playwright-cli open "file://$P"
for wh in "375 812" "768 1024" "1440 900"; do
  playwright-cli resize $wh
  # 0 = no horizontal overflow at this viewport (the engine's document-level check)
  playwright-cli eval "document.documentElement.scrollWidth - document.documentElement.clientWidth"
  # [] = no element overflows (the engine's element-level check, same predicate)
  playwright-cli eval "[...document.querySelectorAll('*')].filter(e=>e.scrollWidth>e.clientWidth&&e.clientWidth>0).map(e=>e.tagName+'.'+e.className).slice(0,10)"
  # [] = every tappable control is >= 44px tall (the engine's touch-target check, same selector list)
  playwright-cli eval "[...document.querySelectorAll('button,.chip,.tab-btn,a.btn')].filter(e=>{const r=e.getBoundingClientRect();return r.height>0&&r.height<44}).map(e=>e.className||e.tagName)"
done
```

Read the numbers, do not read the CSS by eye — a fix that "should" work is CANNOT-TELL until
`scrollWidth == clientWidth` at 375. Then say what you measured, at which viewport, in your reply.

## 5. Rules that come with it
- **Fix on the served page, not the file** if the two differ — the `/pages/` route injects its own
  padding; a probe on `file://` can pass while the served page fails. When in doubt, wait for the
  host engine (it audits what QA audits).
- A QA NO-SHIP names the selector and the viewport. Re-run §4 on that exact pair; reply with the
  before/after numbers. "Fixed" without a number is the claim the 2026-09-05 distill flagged.
- Do not fork this engine into a per-tenant script. If a check is missing, say so to `host@mesh`;
  it gets added to the canonical engine and this copy is re-synced (`check-sync.sh`).

## Requesting a SHIP re-audit after a fix (2026-09-09)

`quality-assurance-manager@mesh` is a cron role agent with **no inbox reader** — a mesh message asking for a re-audit is never seen (josh-desk-1's 042 sat 14 h). Its engine, `scripts/mesh-nightly-shipped/qa-audit-next.sh` (host cron :15/:45, one audit per run), takes **PENDING rows in `/mnt/agent-mesh/agents/quality-assurance-manager/audit-queue.jsonl` first**. To request a re-audit of a fixed page, append one JSON line (never rewrite the file):

```
{"artifact_name":"<page>.html","artifact_path":"/mnt/clients/<t>/openvoiceui/canvas-pages/<page>.html","client":"<t>","size_kb":<n>,"has_chart":false,"has_tab":false,"has_theme":false,"queued_at":"<ISO>","status":"PENDING","reason":"SHIP re-audit after fixing <what>"}
```

From a desk without host-path access, send the line to `host@mesh` (KIND task) and host appends it. The verdict lands as `mesh/QUALITY/<page>-audit-<date>.json`; `qa-gate-enforce.sh` (03:30Z) reads the newest. A cached SHIP (<7 d, artifact unchanged) is skipped — a re-audit only runs when the file changed or a PENDING row names it.

## 6. Prove THIS install actually works — `self-test.sh` (2026-09-10)

Added by pledge `687e2fd3` (2026-09-09 nightly meeting SHARE, quality-assurance-manager@mesh —
"every install proves itself"). A node that has this skill directory does not necessarily have a
working Playwright + chromium underneath it; a copied engine file proves nothing about whether it
can run where it landed.

```bash
bash /mnt/system/base/skills/page-audit-harness/self-test.sh
```

Runs the engine against two fixtures shipped alongside it in this same directory:
- `qa-canary-fixture.html` — deliberately broken (missing `<title>`, failing contrast, undersized
  touch target). Must verdict **NO-SHIP**.
- `qa-known-good-fixture.html` — clean minimal page. Must verdict **SHIP**.

Three outcomes, never just two:
- **CANNOT-RUN** (exit 3) — prereq missing (`python3`, the `playwright` module, or no chromium
  build under `~/.cache/ms-playwright`), names the exact missing piece. Never a false pass.
- **FAIL** (exit 1) — engine ran but got a verdict backwards (regression or over-firing).
- **PASS** (exit 0) — both fixtures verdict correctly; this install's auditor discriminates.

Measured on the host VPS 2026-09-10: canary → `NO-SHIP` (1 CRITICAL, 2 HIGH), known-good →
`SHIP` (0 findings), self-test → `PASS`. No other node on the fleet has been confirmed to run it
— every openclaw/openvoiceui container and all three webtop desktops lack Python Playwright (§2);
run `self-test.sh` on any node before trusting a page-audit-harness install there, and expect
`CANNOT-RUN` off the host unless that node has separately installed Playwright + chromium.

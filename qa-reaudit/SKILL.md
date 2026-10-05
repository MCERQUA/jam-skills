# qa-reaudit — 3-viewport browser audit battery

Reusable Playwright audit for ANY user-facing HTML artifact (canvas pages, brand
reports, dashboards, mockups). Canonical copy: `/mnt/system/base/skills/qa-reaudit/qa-reaudit.py`.
Owner: quality-assurance-manager@mesh. Routed share from the 2026-09-30 mesh meeting
(host task: "turn qa-reaudit.py into a shared skill / fleet install").

## Usage

```sh
python3 /mnt/system/base/skills/qa-reaudit/qa-reaudit.py <artifact.html> <client> <outdir>
```

Needs: `playwright` (sync API) + chromium. No keys, no network — runs on `file://`.

## What it checks (per viewport x theme combination)

- Document + per-element horizontal overflow (`scrollWidth > clientWidth`)
- Off-screen visible text nodes (beyond viewport edges)
- WCAG contrast < 4.5:1 on badge-like elements (`.pill .tag .badge .status .mention [class*=sev-] .chip`), with alpha-composited background resolution
- Touch targets < 44px (mobile viewport only)
- Canvas health (non-zero dims + non-empty `toDataURL`)
- Tab invariant (exactly one active panel)
- Purple detection (hue 255-305, project rule: NO purple in UI artifacts)
- Emoji detection in UI text (project rule: NO emojis)
- Render health: runtime `innerText` AND no-JS static text char count — both must read zero before "blank page" is reported (kills harness false-CRITICALs)
- Lead-form AUTOFILL probe (2026-10-05): fills visible fields with the NATIVE value setter, dispatches NO input/change events, asserts a gated submit/next control enables. Stays disabled → HIGH `form-autofill-deadlock` (React state only moves on input events, so autofill/pre-hydration users cannot submit; found on 16 of ~670 sites where every typing test passed). Conservative: ungated forms skipped, needs >=2 visible fields.
- Structural review-section detector (2026-10-05, josh-desk-1 routed share): JSON-LD Review/AggregateRating, schema.org microdata, card clusters where >=half the cards carry a rating signal — catches review blocks headed anything (word-presence checks miss 11-of-12 style). OBSERVATION-grade: lands in `review_sections` in audit-report.json, never a severity.
- Self-test: `sh self-test.sh` — runs the engine on three in-dir fixtures (autofill deadlock = must NO-SHIP, autofill-friendly interval validator = must SHIP with the probe proven exercised, review sections = must detect "What Our Clients Say" and NOT the services negative control). Fixtures travel with the engine; do not separate them.

Severity: CRITICAL = doc overflow / blank page / tab invariant broken; HIGH = element
overflow (non-clipped), offscreen text, contrast, touch, canvas, purple, emoji;
MEDIUM = clipped (`overflow-x: hidden`) residual overflow.

Verdict: SHIP iff 0 CRITICAL and 0 HIGH. Outputs `audit-report.json`, `audit-report.md`,
and `screenshots/<viewport>_<theme>.png` into `<outdir>`.

## Gotchas baked in (do not remove when forking)

- overflow-x:hidden elements CLIP — that is MEDIUM, not HIGH (paint-underlap impossible).
- Content inside an `overflow-x: auto/scroll` rail is reachable by design — not offscreen.
- Theme detection: clicks the toggle, compares body background; if the click does not
  change the background, light theme is skipped WITH a recorded reason, never silently.
- The no-JS static text count is the second instrument — `innerText==0` from a failed
  harness load is CANNOT-TELL, not a bug.

## Convergence note

Older drifted copies: quality-assurance-manager workspace `artifacts/qa-reaudit-2026-09-27.py`
and `artifacts/qa-reaudit-2026-09-28.py` (dated snapshots, historical). Canonical is THIS
file; `artifacts/qa-reaudit.py` in the QA workspace symlinks here. Do not start new forks —
parameterize, don't copy.

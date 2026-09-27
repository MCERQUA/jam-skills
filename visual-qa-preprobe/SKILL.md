# visual-qa-preprobe — pre-ship self-probe for visual artifacts

Run the QA Manager's OWN checks on your canvas page / report BEFORE submitting it for
formal audit. If your pre-probe passes here, the formal audit passes too — same instrument,
same predicates. This kills NO-SHIP round-trips.

## What it is

`qa_preprobe.py` — Playwright headless-Chromium audit. Per combination of
viewport (375x812 mobile / 768x1024 tablet / 1440x900 desktop) x theme (dark + light when a
toggle exists) it captures a full-page screenshot and checks:

- document horizontal overflow (`scrollWidth > clientWidth`)
- per-element overflow (skips intentional `overflow-x: auto/scroll` rails)
- off-screen text nodes
- WCAG contrast < 4.5:1 on pill/tag/badge/status/chip/sev-* elements (composited backgrounds)
- touch targets < 44px in BOTH width AND height at mobile (the predicate desk pre-probes
  most often get wrong is width — 2026-09-27 incident: a 39px-wide chip passed a
  height-only probe and failed the formal audit)
- canvas health (non-zero dims + non-empty toDataURL)
- tab invariant (exactly one active panel)
- purple rule (hue 255-305 with real saturation — hard project rule)
- emoji rule (astral emoji + FE0F sequences in visible UI text — hard project rule)

Two-instrument render health: a blank runtime read is only CRITICAL if static text is also
zero; otherwise it is CANNOT-TELL (harness failure), never reported as a page bug.

## Usage

    python3 qa_preprobe.py <artifact.html> <client-name> <output-dir>

Needs: `python3` + `playwright` (with chromium installed). Output: `audit-report.json`,
`audit-report.md` (verdict line + bug list), `screenshots/`.

## Verdict semantics

- `SHIP` in the pre-probe means the formal audit will not flag critical/high — submit with
  confidence and note "pre-probe clean" in your request.
- `NO-SHIP` means fix the listed bugs AT THE ROOT RULE (no !important piles at the bottom of
  the stylesheet) and re-run. Submit only when clean.
- Known instrument artifacts (do NOT fix these; they are documented so you can recognize them):
  - `text-overflow: ellipsis` elements produce offscreen/element-overflow flags whose DOM
    ranges extend past the clip even though the paint is ellipsized. If the element computes
    `text-overflow: ellipsis` + `overflow: hidden`, the flag is an artifact.
  - `scrollWidth > clientWidth` with computed `overflow: visible` paints fully — check WHERE
    the painted edge lands before calling it a bug.
  - `section`-level scrollWidth excess with zero overflowing element children is usually a
    decorative pseudo-element clipped by the section's own `overflow-x: hidden` — by design.

## Provenance

Maintained by quality-assurance-manager@mesh. This is the same harness the formal audit
runs (workspace copy: /mnt/agent-mesh/workspaces/quality-assurance-manager/artifacts/qa-reaudit.py).
Predicate changes land here and in the formal audit together — they cannot drift.
First fleet install 2026-09-27 (routed share from 2026-09-26 mesh meeting).

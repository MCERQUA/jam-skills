# qa-reaudit — parameterized 3-viewport Playwright QA battery

Re-audit a visual artifact (canvas page, brand report) across mobile 375x812, tablet
768x1024, desktop 1440x900 and emit a JSON verdict (SHIP / NO-SHIP) with per-check
findings. The workflow it implements: docs/jambot/visual-artifact-qa-workflow.md.
Shared 2026-09-24 from quality-assurance-manager@mesh (pledge 9e025325).

## Usage

```bash
python3 qa-reaudit.py <artifact.html> <client> <outdir>
```

- `<artifact.html>` — file to audit (a live copy, not the QA reference).
- `<client>` — client slug (used in the output report metadata).
- `<outdir>` — directory for `audit-report.json` + screenshots.

## What it checks

- horizontal overflow (document + per-element, scroll-rail aware)
- off-screen text nodes
- body background does not flip between theme classes (theme leak)
- render health: body innerText length AND a static no-JS character count
  (a failed harness load is indistinguishable from a blank page by runtime
  read alone — 2026-09-21 storehouse false-CRITICAL)
- purple hue detection (project rule: no purple in UI artifacts)

## Requirements

- playwright + chromium installed in the calling lane
- read access to the artifact

## Re-audit rule

A NO-SHIP audit is only cleared by a re-audit at the SAME scope that ran the
original (same viewports, same checks). Success = 0 CRITICAL and 0 HIGH.
Never clear a gate from the fixer's self-report.

## Companion

`qa-noship-age-scan.sh` (quality-assurance-manager workspace) — daily scanner over
`/mnt/agent-mesh/mesh/QUALITY/*.json` sorting stale NO-SHIP verdicts into
RETIRED / AWAITING-RE-AUDIT / STAGNANT, one digest per class per run.

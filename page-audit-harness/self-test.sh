#!/usr/bin/env bash
# self-test.sh — proves an install of the page-audit-harness skill actually works,
# instead of trusting that the files copied over correctly.
#
# Origin: pledge 687e2fd3 (2026-09-09 nightly meeting), SHARE from
# quality-assurance-manager@mesh, folded in by host@mesh 2026-09-10.
# The engine copy + the canonical original already existed here from an earlier
# pledge (40dc413d); this script + the paired known-good fixture are what was
# still missing — a canary alone only proves defects are CAUGHT, not that a
# clean page is correctly cleared.
#
# Contract:
#   - Prereqs missing (python3, the `playwright` module, or a downloaded
#     chromium build)  -> print CANNOT-RUN + the exact missing piece, exit 3.
#     NEVER print a false PASS when the harness cannot actually execute.
#   - Engine runs but the canary comes back SHIP (should be NO-SHIP)          -> FAIL, exit 1.
#   - Engine runs but the known-good fixture comes back NO-SHIP (should SHIP) -> FAIL, exit 1.
#   - Both correct -> PASS, exit 0.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE="$HERE/qa-audit-engine.py"
CANARY="$HERE/qa-canary-fixture.html"
GOOD="$HERE/qa-known-good-fixture.html"
DATE="$(date -u +%Y-%m-%d)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() { echo "FAIL: $*"; exit 1; }
cannot_run() { echo "CANNOT-RUN: $*"; exit 3; }

command -v python3 >/dev/null 2>&1 || cannot_run "python3 not found on PATH"

python3 -c 'import playwright' >/dev/null 2>&1 \
  || cannot_run "python3 'playwright' module not importable (pip install playwright / this node has no Python Playwright — see page-audit-harness/SKILL.md §2, host-only by design)"

# A downloaded chromium build must exist under ms-playwright cache, or launch will fail.
CACHE="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"
if [ ! -d "$CACHE" ] || ! ls "$CACHE" 2>/dev/null | grep -qi '^chromium'; then
  cannot_run "no chromium build found under $CACHE (run: python3 -m playwright install chromium)"
fi

[ -f "$ENGINE" ] || cannot_run "engine missing: $ENGINE"
[ -f "$CANARY" ] || cannot_run "canary fixture missing: $CANARY"
[ -f "$GOOD" ] || cannot_run "known-good fixture missing: $GOOD"

echo "--- running engine against canary (expect NO-SHIP) ---"
python3 "$ENGINE" "$CANARY" --client selftest --date "$DATE" \
  > "$TMPDIR/canary.json" 2>"$TMPDIR/canary.err"
canary_verdict="$(python3 -c "import json,sys; print(json.load(open('$TMPDIR/canary.json'))['verdict'])" 2>/dev/null)"
cat "$TMPDIR/canary.json"
if [ "$canary_verdict" != "NO-SHIP" ]; then
  cat "$TMPDIR/canary.err" >&2
  fail "canary verdict was '$canary_verdict', expected NO-SHIP — the auditor is not catching known defects (regression)"
fi

echo "--- running engine against known-good fixture (expect SHIP) ---"
python3 "$ENGINE" "$GOOD" --client selftest --date "$DATE" \
  > "$TMPDIR/good.json" 2>"$TMPDIR/good.err"
good_verdict="$(python3 -c "import json,sys; print(json.load(open('$TMPDIR/good.json'))['verdict'])" 2>/dev/null)"
cat "$TMPDIR/good.json"
if [ "$good_verdict" != "SHIP" ]; then
  cat "$TMPDIR/good.err" >&2
  fail "known-good fixture verdict was '$good_verdict', expected SHIP — the auditor is over-firing (false positives)"
fi

echo "PASS: canary=NO-SHIP, known-good=SHIP — this install's auditor discriminates correctly."
exit 0

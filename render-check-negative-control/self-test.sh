#!/usr/bin/env bash
# self-test.sh — proves render-check.py actually discriminates broken from fixed, in BOTH
# modes, and refuses to call it PASS when it cannot discriminate.
#
# A detector that has never been shown known-bad input is not evidence it can see one — the
# ICA field-dock incident (2026-09-15) shipped for 7 hours because the checker that should have
# caught it had never actually failed on anything. This script is the receipt that this one has.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

RC=render-check.py
F=fixtures
PASS=0
FAIL=0

check() {
  local label="$1" expect_exit="$2"; shift 2
  echo "=== $label ==="
  set +e
  out=$(python3 "$RC" "$@" 2>&1)
  actual_exit=$?
  set -e
  echo "$out" | sed 's/^/    /'
  if [ "$actual_exit" -eq "$expect_exit" ]; then
    echo "  [PASS] exit=$actual_exit (expected $expect_exit)"
    PASS=$((PASS+1))
  else
    echo "  [FAIL] exit=$actual_exit (expected $expect_exit)"
    FAIL=$((FAIL+1))
  fi
  echo
}

echo "############################################"
echo "# host mode (real headless chrome)"
echo "############################################"
check "host: OLD broken / NEW fixed -> PASS (0)"        0 --old "$F/broken.html"     --new "$F/fixed.html"     --mode host
check "host: OLD broken / NEW broken -> FAIL (2)"        2 --old "$F/broken.html"     --new "$F/broken.html"    --mode host
check "host: both pass -> CANNOT-TELL (3)"                3 --old "$F/both-ok-a.html" --new "$F/both-ok-b.html" --mode host

echo "############################################"
echo "# tenant mode (node --check only, no browser)"
echo "############################################"
check "tenant: OLD broken / NEW fixed -> PASS (0)"       0 --old "$F/broken.html"     --new "$F/fixed.html"     --mode tenant
check "tenant: OLD broken / NEW broken -> FAIL (2)"       2 --old "$F/broken.html"     --new "$F/broken.html"    --mode tenant
check "tenant: both pass -> CANNOT-TELL (3)"               3 --old "$F/both-ok-a.html" --new "$F/both-ok-b.html" --mode tenant

echo "############################################"
echo "# real incident artifact (read-only, not modified)"
echo "############################################"
ICA_OLD=/mnt/clients/ica/openvoiceui/canvas-pages/field-dock.html.bak-pre-syntaxfix-20260915T031332Z
ICA_NEW=/mnt/clients/ica/openvoiceui/canvas-pages/field-dock.html
if [ -f "$ICA_OLD" ] && [ -f "$ICA_NEW" ]; then
  check "real ICA field-dock (pre-syntaxfix vs live) host mode -> PASS (0)"   0 --old "$ICA_OLD" --new "$ICA_NEW" --mode host
  check "real ICA field-dock (pre-syntaxfix vs live) tenant mode -> PASS (0)" 0 --old "$ICA_OLD" --new "$ICA_NEW" --mode tenant
else
  echo "  SKIPPED: ICA fixture files not present on this host ($ICA_OLD)"
fi

echo "############################################"
echo "# no-capability path (neither chrome nor node visible) -> CANNOT-TELL"
echo "############################################"
set +e
python3 - "$F/broken.html" "$F/fixed.html" <<'PYEOF'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('rc', 'render-check.py')
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)
rc.find_chrome = lambda: None
rc.find_node = lambda: None
code = rc.negative_control(Path(sys.argv[1]), Path(sys.argv[2]), 'auto', None)
sys.exit(code)
PYEOF
ncrc=$?
set -e
if [ "$ncrc" -eq 3 ]; then
  echo "  [PASS] no-capability -> CANNOT-TELL (exit 3)"
  PASS=$((PASS+1))
else
  echo "  [FAIL] no-capability -> exit $ncrc (expected 3)"
  FAIL=$((FAIL+1))
fi
echo

echo "############################################"
echo "SELF-TEST SUMMARY: $PASS passed, $FAIL failed"
echo "############################################"
[ "$FAIL" -eq 0 ]

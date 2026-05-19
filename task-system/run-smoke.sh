#!/bin/bash
# Run the E2E smoke test with the right PYTHONPATH.
# Each snapshot was built as a flat layout under /agent-desk/snapshots/; host's
# deploy splits them into subdirs, so cross-snapshot imports need PYTHONPATH.
#
# Usage:
#   bash /mnt/system/base/skills/task-system/run-smoke.sh
#   bash /mnt/system/base/skills/task-system/run-smoke.sh --tenant josh
#
# (--tenant defaults to josh; seam-a-poc was deployed to josh's workspace first.)

set -euo pipefail

TENANT="${TENANT:-josh}"
while [ $# -gt 0 ]; do
  case "$1" in
    --tenant) TENANT="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

BASE=/mnt/system/base/skills/task-system
SEAM_A_DIR="/mnt/clients/${TENANT}/openclaw/workspace/scripts/seam-a-poc"

if [ ! -d "$SEAM_A_DIR" ]; then
  echo "ERROR: seam-a-poc not deployed to /mnt/clients/${TENANT}/... — deploy it there first" >&2
  exit 1
fi

export PYTHONPATH="$BASE/schema:$BASE/scaffold:$BASE/voice-active:$SEAM_A_DIR"

echo "==> Running task-system v0.1.1 verification (tenant=$TENANT)"
echo "    PYTHONPATH=$PYTHONPATH"
echo

OK=0; FAIL=0
run_test() {
  local label="$1"; shift
  echo "--- $label ---"
  if "$@" 2>&1 | tail -5; then
    OK=$((OK+1)); echo "  ✓ $label"
  else
    FAIL=$((FAIL+1)); echo "  ✗ $label"
  fi
  echo
}

run_test "1/5 canonical-schema"    python3 "$BASE/schema/test_canonical_schema.py"
run_test "2/5 tenant-scaffolder"   python3 "$BASE/scaffold/test_scaffolder.py"
run_test "3/5 voice-active"        python3 "$BASE/voice-active/test_voice_active.py"
run_test "4/5 seam-a-poc"          python3 "$SEAM_A_DIR/test_seam_a.py"
run_test "5/5 E2E smoke"           python3 "$BASE/smoke-test/smoke_test.py"

echo "================================================"
echo "DONE — $OK ok, $FAIL failed"
echo "================================================"
exit $FAIL

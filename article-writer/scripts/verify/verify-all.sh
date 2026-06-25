#!/usr/bin/env bash
# verify-all.sh — run ALL deterministic blog-factory gates in order, FAIL-CLOSED.
#
# No LLM. Each gate is a standalone script that exits 0=PASS / 1=FAIL. This runner
# executes them all, prints a per-gate summary table, and exits non-zero if ANY gate
# fails. An agent (or the orchestrator) treats a non-zero exit as "DO NOT PUBLISH".
#
# Usage:  verify-all.sh <work_dir> [--skip-live-links]
#   --skip-live-links : skip the HTTP broken-link scan (offline / pre-deploy dry runs
#                       where outbound liveness can't be reached). Authority + structure
#                       gates still run. Use sparingly — live deploy must run it.
#
# Exit:   0 = ALL gates PASS, 1 = at least one FAIL
set -uo pipefail
WORK_DIR="${1:?usage: verify-all.sh <work_dir> [--skip-live-links]}"
shift || true
SKIP_LIVE=0
for a in "$@"; do [ "$a" = "--skip-live-links" ] && SKIP_LIVE=1; done

DIR="$(cd "$(dirname "$0")" && pwd)"
declare -a NAMES RESULTS

run_gate () {
  local name="$1"; shift
  echo
  echo "######################################################################"
  echo "# RUN GATE: $name"
  echo "######################################################################"
  "$@"
  local rc=$?
  NAMES+=("$name")
  RESULTS+=("$rc")
  return $rc
}

run_gate "components"      python3 "$DIR/check-components.py"      "$WORK_DIR"      || true
run_gate "internal-links"  python3 "$DIR/check-internal-links.py"  "$WORK_DIR"      || true
run_gate "authority"       python3 "$DIR/check-authority.py"       "$WORK_DIR"      || true
run_gate "schema"          python3 "$DIR/check-schema.py"          "$WORK_DIR"      || true
if [ "$SKIP_LIVE" -eq 1 ]; then
  echo; echo "# (broken-link-scan SKIPPED via --skip-live-links)"
  NAMES+=("broken-links"); RESULTS+=("-1")
else
  run_gate "broken-links"  bash "$DIR/check-links.sh"              "$WORK_DIR"      || true
fi

echo
echo "######################################################################"
echo "# VERIFY-ALL SUMMARY  ($WORK_DIR)"
echo "######################################################################"
fail=0
for i in "${!NAMES[@]}"; do
  rc="${RESULTS[$i]}"
  if [ "$rc" = "0" ]; then st="PASS"
  elif [ "$rc" = "-1" ]; then st="SKIP"
  else st="FAIL"; fail=$((fail+1)); fi
  printf "  %-16s %s\n" "${NAMES[$i]}" "$st"
done
echo "######################################################################"
if [ "$fail" -gt 0 ]; then
  echo "VERDICT: FAIL — $fail gate(s) failed. DO NOT PUBLISH."
  exit 1
fi
echo "VERDICT: PASS — all gates green. Safe to publish."
exit 0

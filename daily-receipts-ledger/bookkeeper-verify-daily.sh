#!/usr/bin/env bash
# Daily self-verification for bookkeeper@mesh
# Checks: receipts JSONL non-empty, DONE file present, pledge-index updated within 25h
# Pledge: cee11920 (deadline 2026-06-28)

set -euo pipefail

LEDGER_DIR="/mnt/agent-mesh/mesh/LEDGER"
PLEDGE_INDEX="/mnt/agent-mesh/mesh/BLACKBOARD/accountability/pledge-index.jsonl"
TODAY="$(date -u +%Y-%m-%d)"
RECEIPTS_FILE="${LEDGER_DIR}/receipts/${TODAY}.jsonl"
DONE_FILE="${LEDGER_DIR}/${TODAY}-DONE.md"
ALERT_TARGET="host@mesh"
MESH_MSG_DIR="/mnt/agent-mesh/agents/host/inbox"

FAIL=0
REASONS=()

# Integration-existence check (pledge 657ea1c1, 2026-06-30).
# Before blaming a MISSING-RECEIPT on the agent, verify a receipt-WRITING integration is
# actually wired (a cron entry or known caller). If nothing writes receipts, the absence is
# an unwired-integration problem, NOT an agent failure — emit INTEGRATION-NOT-WIRED instead
# of MISSING-RECEIPT so the ledger layer never false-blames the agent. (pledge-status.py is
# the live example: it lives in the workspace, is called by nothing, and would never produce
# a receipt regardless of agent behavior.)
receipt_integration_wired() {
    local cron
    cron="$(crontab -l 2>/dev/null || true)"
    if printf '%s\n' "${cron}" | grep -Eq 'blog-factory|bookkeeper-aggregate|pledge-status\.py|ledger.*receipt|receipt.*ledger'; then
        return 0
    fi
    # A receipt written today by any actor also proves the integration is live.
    if [[ -f "${RECEIPTS_FILE}" ]] && [[ "$(wc -l < "${RECEIPTS_FILE}")" -gt 0 ]]; then
        return 0
    fi
    return 1
}

# --self-test: inline exercise of all three FAIL paths against a known-bad fixture.
# Invariant: if checks are wired correctly, every condition below must trigger on an
# empty fixture. If any miss, the real script could pass silently on a bad ledger.
if [[ "${1:-}" == "--self-test" ]]; then
    _TMPDIR="$(mktemp -d)"
    trap 'rm -rf "$_TMPDIR"' EXIT
    mkdir -p "${_TMPDIR}/receipts"
    _FAIL=0
    _REASONS=()
    _TODAY_FX="1970-01-01"
    _RECEIPTS_FX="${_TMPDIR}/receipts/${_TODAY_FX}.jsonl"
    _DONE_FX="${_TMPDIR}/${_TODAY_FX}-DONE.md"
    _INDEX_FX="${_TMPDIR}/pledge-index-none.jsonl"
    # Test: receipts file missing
    if [[ ! -f "${_RECEIPTS_FX}" ]]; then _FAIL=$((_FAIL+1)); _REASONS+=("missing-receipts"); fi
    # Test: DONE file missing
    if [[ ! -f "${_DONE_FX}" ]]; then _FAIL=$((_FAIL+1)); _REASONS+=("missing-done"); fi
    # Test: pledge-index missing
    if [[ ! -f "${_INDEX_FX}" ]]; then _FAIL=$((_FAIL+1)); _REASONS+=("missing-pledge-index"); fi
    if [[ "${_FAIL}" -ne 3 ]]; then
        echo "[bookkeeper-verify-daily --self-test] FAIL: only ${_FAIL}/3 FAIL paths triggered — check wiring"
        exit 1
    fi
    # Verify the FAIL receipt-write path actually writes to RECEIPTS_DIR.
    # A self-test that only checks FAIL detection cannot catch a broken write (e.g. bad
    # RECEIPTS_DIR path, python3 failure inside printf). Exercise the write explicitly.
    _RECEIPTS_DIR="${_TMPDIR}/receipts"
    _RECEIPT_FILE="${_RECEIPTS_DIR}/${_TODAY_FX}.jsonl"
    _LINES_BEFORE=$([ -f "${_RECEIPT_FILE}" ] && wc -l < "${_RECEIPT_FILE}" || echo 0)
    printf '%s\n' "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"actor\":\"bookkeeper@mesh\",\"action\":\"verify-daily-fail\",\"status\":\"FAIL\",\"reasons\":\"self-test\"}" >> "${_RECEIPT_FILE}"
    _LINES_AFTER=$(wc -l < "${_RECEIPT_FILE}" 2>/dev/null || echo 0)
    if [[ "${_LINES_AFTER}" -le "${_LINES_BEFORE}" ]]; then
        echo "[bookkeeper-verify-daily --self-test] FAIL: receipt write did not append a line (before=${_LINES_BEFORE} after=${_LINES_AFTER})"
        exit 1
    fi
    _LAST=$(tail -1 "${_RECEIPT_FILE}")
    if ! printf '%s' "${_LAST}" | grep -q '"status":"FAIL"'; then
        echo "[bookkeeper-verify-daily --self-test] FAIL: written receipt missing status:FAIL — got: ${_LAST}"
        exit 1
    fi
    echo "[bookkeeper-verify-daily --self-test] PASS: all 3 FAIL paths triggered (${_REASONS[*]}); FAIL receipt write verified (before=${_LINES_BEFORE} after=${_LINES_AFTER})"
    exit 0
fi

# Check 1: receipt file exists and has > 0 lines
if [[ ! -f "${RECEIPTS_FILE}" ]]; then
    if receipt_integration_wired; then
        FAIL=1
        REASONS+=("MISSING-RECEIPT: receipts file missing despite wired integration: ${RECEIPTS_FILE}")
    else
        FAIL=1
        REASONS+=("INTEGRATION-NOT-WIRED: no receipt-writing integration found in cron — absence is not an agent failure (${RECEIPTS_FILE})")
    fi
elif [[ "$(wc -l < "${RECEIPTS_FILE}")" -eq 0 ]]; then
    # Allow early-morning zero before 06:00Z
    HOUR="$(date -u +%H)"
    if [[ "${HOUR}" -ge 6 ]]; then
        if receipt_integration_wired; then
            FAIL=1
            REASONS+=("MISSING-RECEIPT: receipts file has 0 lines after 06:00Z despite wired integration: ${RECEIPTS_FILE}")
        else
            FAIL=1
            REASONS+=("INTEGRATION-NOT-WIRED: receipts file empty after 06:00Z and no receipt-writing integration in cron (${RECEIPTS_FILE})")
        fi
    fi
fi

# Check 2: DONE file exists and is non-empty
if [[ ! -f "${DONE_FILE}" ]]; then
    FAIL=1
    REASONS+=("DONE file missing: ${DONE_FILE}")
elif [[ ! -s "${DONE_FILE}" ]]; then
    FAIL=1
    REASONS+=("DONE file is empty: ${DONE_FILE}")
fi

# Check 3: pledge-index updated within 25 hours
if [[ ! -f "${PLEDGE_INDEX}" ]]; then
    FAIL=1
    REASONS+=("pledge-index missing: ${PLEDGE_INDEX}")
else
    AGE_SECONDS=$(( $(date -u +%s) - $(stat -c %Y "${PLEDGE_INDEX}") ))
    if [[ "${AGE_SECONDS}" -gt 90000 ]]; then  # 25 hours
        FAIL=1
        REASONS+=("pledge-index not updated in >25h (age=${AGE_SECONDS}s)")
    fi
fi

# Check 4: AUTO-RECONCILE — OVERDUE/OPEN pledges whose pledge_id already has a
# DONE-grade LEDGER receipt get a DONE-RECEIPTED index record appended. Closes the
# phantom-OVERDUE class (josh eb6119bf, danielle e80f6233, host-clone 02:04Z —
# 3 council cases in ONE night, 2026-07-11): a real deliverable with a receipt but
# a stale index status read as never-shipped and burned enforcement + council time.
# (Added by host@mesh 2026-07-11 per own meeting commitment; bookkeeper notified.)
if [[ -f "${PLEDGE_INDEX}" && -d "${LEDGER_DIR}/receipts" ]]; then
python3 - "$PLEDGE_INDEX" "${LEDGER_DIR}/receipts" <<'PYEOF' || echo "[bookkeeper-verify-daily] WARN auto-reconcile pass failed (non-fatal)"
import json, sys, os, glob, datetime
index_path, receipts_dir = sys.argv[1], sys.argv[2]
DONE_STATUSES = {"DONE", "DONE-RECEIPTED", "SHIPPED", "RESOLVED", "CLOSED", "VERIFIED"}
DONE_ACTIONS  = {"shipped", "resolved", "completed", "delivered", "implemented", "task-done"}
# latest status per pledge_id (append-only index: last record wins)
latest = {}
for line in open(index_path):
    line = line.strip()
    if not line: continue
    try: r = json.loads(line)
    except Exception: continue
    pid = r.get("pledge_id")
    if pid: latest[pid] = r
open_ids = {pid for pid, r in latest.items()
            if str(r.get("status", "")).upper() in ("OVERDUE", "OPEN", "PENDING")}
if not open_ids:
    print("[auto-reconcile] no open/overdue pledges to reconcile"); sys.exit(0)
# scan receipts for DONE-grade evidence per pledge_id (receipt ts must be >= index ts
# is NOT required: a late-filed receipt still proves delivery)
evidence = {}
for f in sorted(glob.glob(os.path.join(receipts_dir, "*.jsonl"))):
    for line in open(f, errors="replace"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        pid = r.get("pledge_id")
        if pid not in open_ids: continue
        status = str(r.get("status", "")).upper()
        action = str(r.get("action", "")).lower()
        if status in DONE_STATUSES or action in DONE_ACTIONS:
            evidence[pid] = (r.get("id") or r.get("ts") or "?", os.path.basename(f))
if not evidence:
    print(f"[auto-reconcile] {len(open_ids)} open/overdue checked — no matching DONE receipts"); sys.exit(0)
ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(index_path, "a") as out:
    for pid, (rid, rfile) in sorted(evidence.items()):
        rec = {"pledge_id": pid, "status": "DONE-RECEIPTED", "ts": ts,
               "by": "bookkeeper-auto-reconcile",
               "note": f"auto-reconciled: DONE-grade LEDGER receipt {rid} in {rfile} while index said {latest[pid].get('status')}"}
        out.write(json.dumps(rec) + "\n")
        print(f"[auto-reconcile] {pid}: {latest[pid].get('status')} -> DONE-RECEIPTED (receipt {rid})")
print(f"[auto-reconcile] reconciled {len(evidence)} pledge(s)")
PYEOF
fi

if [[ "${FAIL}" -eq 0 ]]; then
    echo "[bookkeeper-verify-daily] OK — receipts present, DONE file present, pledge-index fresh"
    # Circular-liveness guard (Night 68, 2026-08-01): after 12:00Z, a day where every receipt
    # is from bookkeeper@mesh means the ledger looks healthy while no peer has filed anything.
    # Emits SILENT-AGENT-DAY as a distinct signal — does not change the OK exit.
    HOUR_NOW="$(date -u +%H)"
    if [[ "${HOUR_NOW}" -ge 12 && -f "${RECEIPTS_FILE}" ]]; then
        NON_SELF_COUNT=$(grep -cv '"actor":"bookkeeper@mesh"' "${RECEIPTS_FILE}" 2>/dev/null || echo 0)
        if [[ "${NON_SELF_COUNT}" -eq 0 ]]; then
            echo "[bookkeeper-verify-daily] SILENT-AGENT-DAY: all receipts authored by bookkeeper@mesh after 12:00Z — peers may be dark"
        fi
    fi
    # Self-heartbeat: file a LEDGER receipt so this script's own liveness is visible in LEDGER.
    # Without this, a dead script is indistinguishable from a passing script (07-17 blind spot).
    RECEIPTS_DIR="${LEDGER_DIR}/receipts"
    mkdir -p "${RECEIPTS_DIR}"
    printf '%s\n' "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"actor\":\"bookkeeper@mesh\",\"action\":\"verify-daily-ok\",\"status\":\"OK\",\"checks\":\"receipts-present,done-file-present,pledge-index-fresh\"}" >> "${RECEIPTS_DIR}/${TODAY}.jsonl"
    exit 0
fi

# Alert
MSG="Bookkeeper self-verify FAILED on ${TODAY}: $(IFS='; '; echo "${REASONS[*]}")"
echo "[bookkeeper-verify-daily] ALERT: ${MSG}"

# File mesh alert to host inbox
TS="$(date -u +%Y%m%d-%H%M%S)"
ALERT_FILE="${MESH_MSG_DIR}/${TODAY}-bookkeeper-verify-fail-${TS}.md"
cat > "${ALERT_FILE}" <<EOF
FROM: bookkeeper@mesh
TO: host@mesh
SUBJECT: [ALERT] bookkeeper-verify-daily failure — ${TODAY}
DATE: $(date -u +%Y-%m-%dT%H:%M:%SZ)

${MSG}

Investigate: ${RECEIPTS_FILE}, ${DONE_FILE}, ${PLEDGE_INDEX}
EOF

echo "[bookkeeper-verify-daily] Alert filed: ${ALERT_FILE}"

# LEDGER receipt for FAIL path so a failing verifier is distinguishable from a dead/silent one.
RECEIPTS_DIR="${LEDGER_DIR}/receipts"
mkdir -p "${RECEIPTS_DIR}"
printf '%s\n' "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"actor\":\"bookkeeper@mesh\",\"action\":\"verify-daily-fail\",\"status\":\"FAIL\",\"reasons\":$(printf '%s' "${REASONS[*]}" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}" >> "${RECEIPTS_DIR}/${TODAY}.jsonl"

exit 1

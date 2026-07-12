#!/usr/bin/env bash
# session-health.sh — read-only session-poison scanner for the hermes fleet.
#
# Detects the two poison vectors from §1A (2026-07-12 recurrence):
#   1. empty-content turns in a session's replayed history (GLM rejects them
#      -> `response.content invalid (not a non-empty list)` -> 30-60s empty turns)
#   2. trailing runs of consecutive user turns (the retry death-spiral: each
#      failed turn stores another ~18KB user row and no assistant reply)
#
# Usage:  bash session-health.sh [tenant ...]     (default: all hermes-* containers)
# Exit:   0 = all clean, 1 = at least one FLAG.
# Read-only — never deletes anything. Recovery (manual, per §1A):
#   sg docker -c "docker exec -u hermes -e HOME=/opt/data hermes-<t> \
#     /opt/hermes/.venv/bin/hermes sessions delete <session> --yes"
set -u

TENANTS=("$@")
if [ ${#TENANTS[@]} -eq 0 ]; then
  mapfile -t TENANTS < <(sg docker -c "docker ps --filter name=hermes- --format '{{.Names}}'" 2>/dev/null | sed 's/^hermes-//')
fi

FAIL=0
for t in "${TENANTS[@]}"; do
  out=$(sg docker -c "docker exec -i hermes-$t python3 - <<'PY'
import sqlite3
db = sqlite3.connect('/opt/data/state.db')
c = db.cursor()
c.execute('SELECT DISTINCT session_id FROM messages')
for (sid,) in c.fetchall():
    c.execute('SELECT role, trim(coalesce(content,\"\"))=\"\" FROM messages WHERE session_id=? ORDER BY rowid', (sid,))
    rows = c.fetchall()
    empty = sum(1 for _, e in rows if e)
    trail = 0
    for role, _ in reversed(rows):
        if role == 'user':
            trail += 1
        else:
            break
    flag = 'FLAG' if (empty > 0 or trail >= 3) else 'ok'
    print(f'{flag}\t{sid}\tmsgs={len(rows)}\tempty={empty}\ttrailing_user={trail}')
PY" 2>/dev/null)
  if [ -z "$out" ]; then
    echo "hermes-$t: ERROR — could not read state.db (container down or path changed)"
    FAIL=1
    continue
  fi
  while IFS= read -r line; do
    echo "hermes-$t: $line"
    case "$line" in FLAG*) FAIL=1;; esac
  done <<< "$out"
done

if [ $FAIL -eq 0 ]; then
  echo "=== session-health: ALL CLEAN ==="
else
  echo "=== session-health: FLAGS FOUND — see §1A of hermes-expert SKILL.md for recovery ==="
  echo "    NOTE: only sessions that get REPLAYED matter operationally — 'main' is the OVU"
  echo "    voice session (the critical one). FLAGs on old test/one-off session ids are inert"
  echo "    unless that session id is reused."
fi
exit $FAIL

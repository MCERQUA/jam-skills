#!/bin/bash
# audit-anchors.sh — drift detection against the values documented in
# /mnt/system/base/skills/hermes-expert/SKILL.md §13B.
#
# Returns 0 if all anchors match. Returns non-zero on first mismatch.
# Output: one line per anchor, PASS or FAIL with the discrepancy.

set -u

PASS=0
FAIL=0

check() {
    local label="$1"
    local expected="$2"
    local actual="$3"
    if echo "$actual" | grep -q "$expected" 2>/dev/null; then
        echo "  PASS  $label  ($expected)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $label"
        echo "        expected: $expected"
        echo "        actual:   $actual"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== hermes-expert audit-anchors (2026-05-23 baseline) ==="
echo

# Hermes runtime version
ver=$(sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes --version 2>/dev/null" 2>/dev/null || echo "unreachable")
check "hermes version" "0.13" "$ver"

# OpenClaw runtime version
ocver=$(sg docker -c "docker exec openclaw-test-dev openclaw --version 2>/dev/null" 2>/dev/null || echo "unreachable")
check "openclaw version" "2026.5.7" "$ocver"

# LLM primary
primary=$(sg docker -c "docker exec openclaw-test-dev openclaw config get agents.defaults.model.primary 2>/dev/null" 2>/dev/null)
check "LLM primary" "zai/glm-5-turbo" "$primary"

# LLM fallback
fb=$(sg docker -c "docker exec openclaw-test-dev openclaw config get agents.defaults.model.fallbacks 2>/dev/null" 2>/dev/null)
check "LLM fallback" "zai_fb/glm-5-turbo" "$fb"

# Hermes binary present at v0.13 path
binpath=$(sg docker -c "docker exec hermes-test-dev test -x /opt/hermes/.venv/bin/hermes && echo present || echo missing" 2>/dev/null)
check "hermes binary path" "present" "$binpath"

# Helper: read a single env var from the hermes container's /opt/data/.env file.
# Hermes reads its own .env at startup; values are NOT necessarily in the
# container's process env. The file is the source of truth.
container_env() {
    sg docker -c "docker exec hermes-test-dev sh -c 'grep \"^$1=\" /opt/data/.env 2>/dev/null | head -1 | cut -d= -f2-'" 2>/dev/null
}

# Z.AI subscription endpoint in hermes container env
endpoint=$(container_env ANTHROPIC_BASE_URL)
check "Z.AI endpoint (container env)" "api.z.ai/api/anthropic" "${endpoint:-missing}"

# ANTHROPIC_API_KEY present in container env (NOT the value — just present)
authkey=$(container_env ANTHROPIC_API_KEY)
check "ANTHROPIC_API_KEY present" "." "${authkey:-missing}"

# API_SERVER_KEY present (v0.13 refuses to start without on non-loopback bind)
serverkey=$(container_env API_SERVER_KEY)
check "API_SERVER_KEY present" "." "${serverkey:-missing}"

# GATEWAY_ALLOW_ALL_USERS set true (we don't gate at Hermes layer)
allowall=$(container_env GATEWAY_ALLOW_ALL_USERS)
check "GATEWAY_ALLOW_ALL_USERS" "true" "${allowall:-missing}"

# MiniMax key MUST NOT be in container env (dropped 2026-05-19).
# Catches the case where container was started before MiniMax purge —
# requires container recreate to clear stale env.
mxincontainer=$(container_env MINIMAX_API_KEY)
if [ -z "$mxincontainer" ]; then
    check "MiniMax key absent from container env" "absent-good" "absent-good"
else
    check "MiniMax key absent from container env" "absent-good" "PRESENT-BAD (recreate container after .openclaw-keys.env purge)"
fi

# Config schema version
schema=$(sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config check 2>&1" 2>/dev/null | grep -i "version" | head -1)
check "config schema" "23" "$schema"

# Live tenant inventory (count must match docs)
count=$(sg docker -c "docker ps --filter name=hermes --format '{{.Names}}'" 2>/dev/null | wc -l)
check "live hermes containers (count)" "1" "$count"

# Rollback image present
rollback=$(sg docker -c "docker images jambot/hermes --format '{{.Repository}}:{{.Tag}}' 2>/dev/null" 2>/dev/null | grep rollback || echo "missing")
check "rollback image preserved" "jambot/hermes:0.6.0-rollback" "$rollback"

# MiniMax key must NOT be active in env (it's dropped)
mxguard=$(grep -E "^MINIMAX_API_KEY=" /mnt/system/base/.openclaw-keys.env 2>/dev/null || echo "absent-good")
check "MiniMax key absent (dropped guard)" "absent-good" "$mxguard"

echo
echo "=== summary: $PASS pass / $FAIL fail ==="
exit "$FAIL"

#!/bin/bash
# audit-anchors.sh — drift detection against the values documented in
# /mnt/system/base/skills/hermes-expert/SKILL.md §13B.
#
# Returns 0 if all anchors match. Returns non-zero on first mismatch.
# Output: one line per anchor, PASS or FAIL with the discrepancy.

set -u

PASS=0
FAIL=0

# Dynamic tenant discovery (2026-07-16, W3): the fleet grew past the original 4 —
# never hardcode tenant lists; per-container anchors cover every RUNNING hermes.
mapfile -t HERMES_TENANTS < <(sg docker -c "docker ps --filter name=hermes- --format '{{.Names}}'" 2>/dev/null | sed 's/^hermes-//' | sort)

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

echo "=== hermes-expert audit-anchors (2026-07-12 baseline — post v0.18.2 roll-forward) ==="
echo

# Hermes runtime version
ver=$(sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes --version 2>/dev/null" 2>/dev/null || echo "unreachable")
check "hermes version" "0.18.2" "$ver"

# OpenClaw runtime version
ocver=$(sg docker -c "docker exec openclaw-test-dev openclaw --version 2>/dev/null" 2>/dev/null || echo "unreachable")
check "openclaw version" "2026.5.7" "$ocver"

# LLM primary
primary=$(sg docker -c "docker exec openclaw-test-dev openclaw config get agents.defaults.model.primary 2>/dev/null" 2>/dev/null)
check "LLM primary" "zai/glm-5-turbo" "$primary"

# LLM fallback
fb=$(sg docker -c "docker exec openclaw-test-dev openclaw config get agents.defaults.model.fallbacks 2>/dev/null" 2>/dev/null)
check "LLM fallback" "zai_fb/glm-5-turbo" "$fb"

# Hermes binary present at v0.13+ path
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
check "config schema" "33" "$schema"

# Live tenant inventory: every PROVISIONED tenant (a /mnt/clients/<t>/hermes/config.yaml
# exists) must have a RUNNING container, and vice versa. (2026-07-16: dynamic — the
# hardcoded "4" went stale the day bhb+koolfoam were provisioned.)
provisioned=$(ls -d /mnt/clients/*/hermes/config.yaml 2>/dev/null | sed 's|/mnt/clients/||;s|/hermes/config.yaml||' | sort | tr '\n' ' ')
running=$(printf '%s ' "${HERMES_TENANTS[@]}")
if [ "$provisioned" = "$running" ]; then
    check "hermes fleet (provisioned==running)" "match" "match"
else
    check "hermes fleet (provisioned==running)" "match" "provisioned:[$provisioned] running:[$running]"
fi

# Rollback path present.
# 2026-07-12: BOTH rollback images (v0.15.2 + 0.6.0-rollback) were PRUNED in the
# /mnt/system disk reclaim. Rollback = rebuild from source dirs (SKILL.md §10A).
# Anchor now checks the rebuild dirs exist (+ per-tenant pre-v0.18.0 backups).
rbdirs="missing"
[ -f /mnt/system/base/hermes-v015-build/Dockerfile ] && [ -f /mnt/system/base/hermes-v0182-build/Dockerfile ] && rbdirs="build-dirs-present"
check "rollback path (pre-roll-20260712 tag + rebuild dirs)" "build-dirs-present" "$rbdirs"

# Plugin gateway.py parity — catalog must match every tenant runtime copy
# (a stale catalog regresses hotfixes on reinstall; SKILL.md §8).
cat_md5=$(md5sum /mnt/system/base/plugin-catalog/hermes-agent/gateway.py 2>/dev/null | cut -c1-8)
parity="in-sync"
for t in "${HERMES_TENANTS[@]}"; do
  t_md5=$(md5sum /mnt/clients/$t/openvoiceui/plugins/hermes-agent/gateway.py 2>/dev/null | cut -c1-8)
  [ "$t_md5" = "$cat_md5" ] || parity="DRIFT:$t=$t_md5,catalog=$cat_md5"
done
check "plugin gateway.py catalog==fleet parity" "in-sync" "$parity"

# agent.reasoning_effort=none in EVERY tenant config (2026-07-17: 6/7 tenants were
# missing it — GLM burns the response on thinking and returns EMPTY content
# ("response.content invalid" → "Empty response from agent" in the voice UI).
# Hermes equivalent of OpenClaw thinkingDefault:"off". Seed+backfill now in
# cont-init (v0182 build); this anchor catches any config rewrite that drops it.
re="all-set"
for t in "${HERMES_TENANTS[@]}"; do
  grep -q 'reasoning_effort' /mnt/clients/$t/hermes/config.yaml 2>/dev/null || re="MISSING:$t"
done
check "agent.reasoning_effort present (all tenants)" "all-set" "$re"

# Z.AI account-B fallback in credential pool with correct base_url (wired 2026-07-12)
poolb=$(sg docker -c "docker exec hermes-test-dev python3 -c \"
import json
e=[x for x in json.load(open('/opt/data/auth.json'))['credential_pool'].get('anthropic',[]) if x.get('label')=='zai-account-B']
print('present:'+e[0].get('base_url','') if e and e[0].get('access_token') else 'missing')\"" 2>/dev/null)
check "Z.AI account-B pool entry (Z.AI base_url)" "present:https://api.z.ai/api/anthropic" "$poolb"

# Replay-sanitize patch live in fleet (root fix for session poison, 2026-07-12)
rs="in"
for t in "${HERMES_TENANTS[@]}"; do
  sg docker -c "docker exec hermes-$t grep -q 'JamBot replay sanitize' /opt/hermes/agent/turn_context.py" 2>/dev/null || rs="MISSING:$t"
done
check "replay-sanitize patch live (all tenants)" "in" "$rs"

# MiniMax key must NOT be active in env (it's dropped)
mxguard=$(grep -E "^MINIMAX_API_KEY=" /mnt/system/base/.openclaw-keys.env 2>/dev/null || echo "absent-good")
check "MiniMax key absent (dropped guard)" "absent-good" "$mxguard"

# OpenClaw-parity anchors (2026-07-12, v0.18.2-jb1 roll): mesh access + approvals off
# + inert sanitize placeholder ("." — the old "(tool call)" got MIMICKED into TTS).
mesh_ok="ok"; appr_ok="ok"; ph_ok="ok"
for t in "${HERMES_TENANTS[@]}"; do
  sg docker -c "docker exec hermes-$t sh -c 'test -d /mnt/agent-mesh && test -x /usr/local/bin/mesh-send'" 2>/dev/null || mesh_ok="MISSING:$t"
  sg docker -c "docker exec hermes-$t grep -A1 '^approvals:' /opt/data/config.yaml" 2>/dev/null | grep -qE "mode: [\"']off[\"']" || appr_ok="MISSING:$t"
  sg docker -c "docker exec hermes-$t grep -q '_m\[.content.\] = \".\"' /opt/hermes/agent/turn_context.py" 2>/dev/null || ph_ok="OLD-PLACEHOLDER:$t"
done
check "mesh parity (mount + mesh CLI, all tenants)" "ok" "$mesh_ok"
check "approvals.mode off (all tenants)" "ok" "$appr_ok"
check "sanitize placeholder inert '.' (all tenants)" "ok" "$ph_ok"

# jb2 anchors (2026-07-16): write-side empty-turn guard + replay-sanitize v2
wg="ok"; s2="ok"
for t in "${HERMES_TENANTS[@]}"; do
  sg docker -c "docker exec hermes-$t grep -q 'JamBot write-side empty-turn guard' /opt/hermes/hermes_state.py" 2>/dev/null || wg="MISSING:$t"
  sg docker -c "docker exec hermes-$t grep -q 'JamBot replay sanitize v2' /opt/hermes/agent/turn_context.py" 2>/dev/null || s2="MISSING:$t"
done
check "write-side empty-turn guard live (jb2, all tenants)" "ok" "$wg"
check "replay-sanitize v2 shape-v3 defense live (jb2, all tenants)" "ok" "$s2"

# Provisioner image pin matches the fleet
pin=$(grep -oE 'f"jambot/hermes:[^"]+"' /home/mike/MIKE-AI/scripts/jambot-provision-service.py | sed 's/^f"//;s/"$//' | head -1)
check "provisioner image pin" "jambot/hermes:v0.18.2-jb2" "$pin"

echo
echo "=== summary: $PASS pass / $FAIL fail ==="
exit "$FAIL"

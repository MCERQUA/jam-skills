#!/usr/bin/env bash
# host-deploy-and-verify.sh — Host-side post-build deploy + verification.
#
# Runs AFTER z-code agent finishes phases 1-7.5 inside openclaw. Owns:
#   8. Quality gate (pnpm build in webdev container — matching pnpm store)
#   9. Deploy (clean install + restart webdev)
#  10. GitHub push (gh CLI on host, not in container)
#  11. Verification (curl every recommended page on real intake.devUrl)
#
# Why on the host: openclaw and webdev have different pnpm stores. Building in
# openclaw against the shared volume corrupts what webdev serves. The fix is to
# do quality-gate + deploy entirely in webdev, where the runtime store matches.
#
# Usage:
#   host-deploy-and-verify.sh --client <name> --project <projectName> \
#       --webdev-container <name> --intake <path> --status <path> --log <path>

set -euo pipefail

CLIENT=""
PROJECT=""
WEBDEV_CONTAINER=""
INTAKE=""
STATUS_FILE=""
LOG_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --client) CLIENT="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --webdev-container) WEBDEV_CONTAINER="$2"; shift 2 ;;
    --intake) INTAKE="$2"; shift 2 ;;
    --status) STATUS_FILE="$2"; shift 2 ;;
    --log) LOG_FILE="$2"; shift 2 ;;
    *) echo "unknown: $1" >&2; exit 2 ;;
  esac
done

[[ -z "$PROJECT" || -z "$WEBDEV_CONTAINER" || -z "$INTAKE" || -z "$STATUS_FILE" ]] && {
    echo "missing required args" >&2; exit 2;
}

LOG_FILE="${LOG_FILE:-/tmp/${PROJECT}-deploy.log}"

log() { printf '[host-deploy %s] %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG_FILE"; }

set_phase() {
    local key="$1" status="$2" msg="$3"
    python3 - <<PY
import json
from datetime import datetime, timezone
with open("$STATUS_FILE") as f: s = json.load(f)
s.setdefault("phases", {})[ "$key" ] = {
    "status": "$status",
    "message": "$msg",
    "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
s["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open("$STATUS_FILE", "w") as f: json.dump(s, f, indent=2)
PY
}

mark_failed() {
    local phase="$1" msg="$2"
    set_phase "$phase" "failed" "$msg"
    python3 - <<PY
import json
from datetime import datetime, timezone
with open("$STATUS_FILE") as f: s = json.load(f)
s["status"] = "failed"
s["error"] = {"phase": "$phase", "message": "$msg",
              "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
with open("$STATUS_FILE", "w") as f: json.dump(s, f, indent=2)
PY
    log "❌ $phase failed: $msg"
}

# ── Verify webdev is running ─────────────────────────────────────────────────
if ! sg docker -c "docker ps --filter 'name=$WEBDEV_CONTAINER' --format '{{.Names}}'" 2>/dev/null \
        | grep -q "^${WEBDEV_CONTAINER}$"; then
    mark_failed deploy "webdev container $WEBDEV_CONTAINER not running"
    exit 1
fi

# ── Pre-deploy: deterministic page generators (no LLM, fast) ─────────────────
# These run on the HOST against the shared volume so they always produce a
# complete site even if the agent skipped them. Idempotent.
PROJECT_DIR="/mnt/clients/$CLIENT/openclaw/workspace/Websites/$PROJECT"
TOOLS_DIR="/mnt/system/base/skills/website-builder/tools"

if [[ -f "$PROJECT_DIR/.intake.json" ]]; then
    log "Pre-deploy: location pages"
    python3 "$TOOLS_DIR/build-location-pages.py" \
        --project "$PROJECT_DIR" \
        --intake "$PROJECT_DIR/.intake.json" >> "$LOG_FILE" 2>&1 || \
        log "  (location pages: tool ran with errors — see log)"

    log "Pre-deploy: blog scaffold"
    python3 "$TOOLS_DIR/build-blog.py" \
        --project "$PROJECT_DIR" \
        --intake "$PROJECT_DIR/.intake.json" >> "$LOG_FILE" 2>&1 || \
        log "  (blog: tool ran with errors — see log)"

    log "Pre-deploy: legal pages (privacy + terms)"
    python3 "$TOOLS_DIR/build-legal-pages.py" \
        --project "$PROJECT_DIR" \
        --intake "$PROJECT_DIR/.intake.json" >> "$LOG_FILE" 2>&1 || \
        log "  (legal: tool ran with errors — see log)"

    log "Pre-deploy: stitch-finalize (logo + dropdowns + footer rewrites + image localization)"
    python3 "$TOOLS_DIR/stitch-finalize.py" \
        --project "$PROJECT_DIR" \
        --intake "$PROJECT_DIR/.intake.json" >> "$LOG_FILE" 2>&1 || \
        log "  (finalize: tool ran with errors — see log)"

    log "Pre-deploy: stitch-fix-links (idempotent re-pass)"
    python3 "$TOOLS_DIR/stitch-fix-links.py" \
        --project "$PROJECT_DIR" \
        --intake "$PROJECT_DIR/.intake.json" >> "$LOG_FILE" 2>&1 || \
        log "  (fix-links: tool ran with errors — see log)"

    log "Pre-deploy: agent-docs (AGENTS.md + site-map + content-registry + site-tools)"
    python3 "$TOOLS_DIR/build-agent-docs.py" \
        --project "$PROJECT_DIR" \
        --intake "$PROJECT_DIR/.intake.json" >> "$LOG_FILE" 2>&1 || \
        log "  (agent-docs: tool ran with errors — see log)"
fi

# ── Phase 8: Quality gate (pnpm build in webdev) ─────────────────────────────
set_phase quality-gate in_progress "pnpm install + build in webdev"
log "Phase 8 quality-gate — clean install + build in $WEBDEV_CONTAINER"
if ! sg docker -c "docker exec $WEBDEV_CONTAINER sh -c 'cd /app/websites/$PROJECT \
    && rm -rf node_modules .next \
    && CI=true pnpm install 2>&1 \
    && pnpm build 2>&1'" >> "$LOG_FILE" 2>&1; then
    mark_failed quality-gate "pnpm build failed in webdev — see $LOG_FILE"
    exit 1
fi
set_phase quality-gate complete "pnpm build green in webdev"
log "✅ quality-gate"

# ── Phase 9: Deploy (restart webdev) ─────────────────────────────────────────
set_phase deploy in_progress "restarting webdev container"
log "Phase 9 deploy — restarting $WEBDEV_CONTAINER"
if ! sg docker -c "docker restart $WEBDEV_CONTAINER" >> "$LOG_FILE" 2>&1; then
    mark_failed deploy "docker restart failed"
    exit 1
fi
sleep 5
set_phase deploy complete "webdev restarted"
log "✅ deploy"

# ── Phase 10: GitHub push (best-effort, host-side gh CLI) ────────────────────
set_phase github-push in_progress "gh push attempt"
log "Phase 10 github-push"
PROJECT_DIR="/mnt/clients/$CLIENT/openclaw/workspace/Websites/$PROJECT"
if [[ -d "$PROJECT_DIR/.git" ]] && command -v gh >/dev/null 2>&1; then
    pushd "$PROJECT_DIR" > /dev/null
    if ! git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        # Defense-in-depth: ensure .gitignore is in place before git add -A so
        # node_modules/.next don't leak into the initial commit (cheer-insurance
        # incident 2026-05-23).
        if [[ ! -f .gitignore ]]; then
            cp /mnt/shared-skills/website-builder/templates/project/.gitignore . 2>/dev/null || true
        fi
        git init -q && git add -A && git commit -qm "initial: from website-builder pipeline"
    fi
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    REPO_NAME=$(basename "$PROJECT_DIR")
    if ! gh repo view "MCERQUA/$REPO_NAME" >/dev/null 2>&1; then
        gh repo create "MCERQUA/$REPO_NAME" --private --source=. --push >> "$LOG_FILE" 2>&1 || true
    fi
    if git push -u origin "$BRANCH" >> "$LOG_FILE" 2>&1; then
        set_phase github-push complete "pushed to MCERQUA/$REPO_NAME ($BRANCH)"
        log "✅ github-push"
    else
        set_phase github-push failed "git push failed (non-blocking)"
        log "⚠ github-push failed but continuing"
    fi
    popd > /dev/null
else
    set_phase github-push complete "skipped — no gh CLI or git repo"
    log "⚠ github-push skipped (no gh CLI or .git)"
fi

# ── Phase 11: Verification (curl every required page on real dev URL) ───────
set_phase verification in_progress "curl every route"
log "Phase 11 verification"

DEV_URL=$(python3 -c "
import json
try:
    d = json.load(open('$INTAKE'))
    print((d.get('devUrl') or '').rstrip('/') or 'https://dev-${CLIENT}.jam-bot.com')
except Exception:
    print('https://dev-${CLIENT}.jam-bot.com')
")

log "  dev URL: $DEV_URL"

# ── Public-DoH pre-check ─────────────────────────────────────────────────────
# The container's local resolver (127.0.0.11 -> host stub 127.0.0.53) has been
# observed serving stale/wrong A records for recently-changed domains, making
# genuinely live sites read back as HTTP 000 "down". Resolve against a public
# DoH endpoint (dns.google, falling back to cloudflare-dns.com) and pin curl to
# that IP with --resolve so verification never trusts the container resolver.
VERIFY_DOMAIN=$(python3 -c "from urllib.parse import urlparse; print(urlparse('$DEV_URL').hostname or '')")

doh_lookup() {
    local domain="$1" ip=""
    for endpoint in "https://dns.google/resolve" "https://cloudflare-dns.com/dns-query"; do
        ip=$(curl -s --max-time 8 -H "accept: application/dns-json" \
                "${endpoint}?name=${domain}&type=A" 2>/dev/null \
             | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    ans = [a['data'] for a in d.get('Answer', []) if a.get('type') == 1]
    print(ans[0] if ans else '')
except Exception:
    print('')
" 2>/dev/null)
        [[ -n "$ip" ]] && break
    done
    echo "$ip"
}

RESOLVE_ARGS=()
if [[ -n "$VERIFY_DOMAIN" ]]; then
    PUBLIC_IP=$(doh_lookup "$VERIFY_DOMAIN")
    if [[ -n "$PUBLIC_IP" ]]; then
        log "  public-DoH: $VERIFY_DOMAIN -> $PUBLIC_IP (bypassing container resolver 127.0.0.11)"
        RESOLVE_ARGS=(--resolve "${VERIFY_DOMAIN}:443:${PUBLIC_IP}" --resolve "${VERIFY_DOMAIN}:80:${PUBLIC_IP}")
    else
        log "  ⚠ public-DoH lookup failed for $VERIFY_DOMAIN — falling back to container resolver (may report false-down on stale records)"
    fi
fi

# Required routes = intake.pages ∪ page-recommendations.md MUST-BUILD list
ROUTES=$(python3 - <<PY
import json, re, sys
d = json.load(open("$INTAKE"))
pages = set(d.get("pages") or [])
recpath = "$PROJECT_DIR/ai/research/page-recommendations.md"
try:
    text = open(recpath).read()
    # Cut off Not-Recommended section
    cut = re.search(r"###\s+Not Recommended", text, re.I)
    if cut: text = text[:cut.start()]
    for m in re.finditer(r"^\|\s*\d+\s*\|\s*[^|]+\|\s*([^|]+)\|", text, re.M):
        u = m.group(1).strip().strip("/").split("/")[0]
        if u and not set(u) <= set("- :"): pages.add(u or "home")
except FileNotFoundError:
    pass
for p in sorted(pages):
    print(p)
PY
)

FAIL=0
TOTAL=0
for slug in $ROUTES; do
    TOTAL=$((TOTAL+1))
    url="${DEV_URL}/${slug}"
    [[ "$slug" == "home" || "$slug" == "" ]] && url="${DEV_URL}/"
    code=$(curl -sk "${RESOLVE_ARGS[@]}" -o /dev/null -w "%{http_code}" --max-time 15 "$url" 2>/dev/null || echo 000)
    if [[ "$code" == "200" ]]; then
        log "  ✓ $code  $url"
    else
        log "  ✗ $code  $url"
        FAIL=$((FAIL+1))
    fi
done

if [[ $FAIL -eq 0 ]]; then
    set_phase verification complete "all $TOTAL routes 200"
    python3 - <<PY
import json
from datetime import datetime, timezone
with open("$STATUS_FILE") as f: s = json.load(f)
s["status"] = "complete"
s["completedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open("$STATUS_FILE", "w") as f: json.dump(s, f, indent=2)
PY
    log "🟢 BUILD COMPLETE — $TOTAL routes 200 at $DEV_URL"
    exit 0
else
    mark_failed verification "$FAIL of $TOTAL routes returned non-200 (see $LOG_FILE)"
    exit 1
fi

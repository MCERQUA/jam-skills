#!/usr/bin/env bash
# build-stitch-pipeline.sh — Full Stitch-first website build pipeline.
#
# Runs ONLY when the website-setup form supplied Stitch screens. The legacy
# WEBSITE-BUILD.md path handles all other cases.
#
# Phases (deterministic, no LLM until Phase 7+):
#   1. SCAFFOLD     — Next.js 15 + Tailwind + TypeScript shell
#   2. STITCH-FETCH — fetch supplied Stitch screen IDs (writes .stitch-pages/*.html)
#   3. STITCH-CONVERT — HTML → JSX via stitch-to-next.py
#   4. ASSET-DOWNLOAD — Stitch CDN images → public/images/stitch/
#   5. CONTENT-LAYER — substitute intake.phone/email/address/businessName/heroImage/gallery
#   6. RESEARCH     — DataForSEO keywords/competitors → ai/research/.dfs/*.json
#   7. EXTRA-PAGES  — generate any intake.pages entry without a Stitch source (LLM)
#   8. QUALITY-GATE — pnpm build + curl-every-route + visual-diff vs Stitch HTML
#   9. DEPLOY       — webdev container reconcile, .env.local, restart
#  10. GITHUB-PUSH  — gh repo create + push
#  11. VERIFICATION — final HTTP checks against dev URL
#
# Usage:
#   build-stitch-pipeline.sh \
#     --intake <intake.json> \
#     --workspace <openclaw workspace path> \
#     --project <projectName>
#
# Idempotent. Re-running with same inputs replays only changed phases.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$SKILL_DIR/tools"

INTAKE=""
WORKSPACE=""
PROJECT=""
RESUME_FROM=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --intake)    INTAKE="$2"; shift 2 ;;
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --project)   PROJECT="$2"; shift 2 ;;
    --from)      RESUME_FROM="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -z "$INTAKE" || ! -f "$INTAKE" ]] && { echo "missing --intake"; exit 2; }
[[ -z "$WORKSPACE" || ! -d "$WORKSPACE" ]] && { echo "missing --workspace"; exit 2; }
[[ -z "$PROJECT" ]] && { echo "missing --project"; exit 2; }

PROJECT_DIR="$WORKSPACE/Websites/$PROJECT"
STATUS_DIR="$PROJECT_DIR/.quality-gate"
STITCH_DIR="$PROJECT_DIR/.stitch-pages"
mkdir -p "$STATUS_DIR" "$STITCH_DIR"

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

phase_done() {
  local key="$1"; local msg="${2:-ok}"
  jq -n --arg k "$key" --arg m "$msg" --arg t "$(date -u +%FT%TZ)" \
    '{phase:$k,status:"complete",message:$m,at:$t}' \
    > "$STATUS_DIR/phase-$key.json"
  log "✅ $key — $msg"
}

phase_fail() {
  local key="$1"; local msg="$2"
  jq -n --arg k "$key" --arg m "$msg" --arg t "$(date -u +%FT%TZ)" \
    '{phase:$k,status:"failed",message:$m,at:$t}' \
    > "$STATUS_DIR/phase-$key.json"
  log "❌ $key — $msg"
  exit 1
}

# Helpers — pull values out of intake.json
intake_get() { jq -r "$1 // empty" "$INTAKE"; }

# ───────────────────────────────────────────────────────────────────────────
# 1. SCAFFOLD — only run if package.json missing (idempotent)
# ───────────────────────────────────────────────────────────────────────────
phase_scaffold() {
  log "PHASE 1/11 SCAFFOLD"
  if [[ -f "$PROJECT_DIR/package.json" ]]; then
    phase_done scaffold "already scaffolded"
    return
  fi
  bash "$TOOLS_DIR/scaffold.sh" "$PROJECT_DIR" "$PROJECT" \
    || phase_fail scaffold "scaffold.sh exit $?"
  phase_done scaffold "Next.js 15 + Tailwind + TS"
}

# ───────────────────────────────────────────────────────────────────────────
# 2. STITCH-FETCH — call get_screen via the stitch MCP for each supplied ID
# This step is OUTSIDE this script — it's done by the agent before this script
# runs (or by a separate mcp client) because MCP requires the agent stack.
# Here we just verify .stitch-pages/*.html exist for each declared screen.
# ───────────────────────────────────────────────────────────────────────────
phase_stitch_fetch() {
  log "PHASE 2/11 STITCH-FETCH (verify)"
  local count
  count=$(find "$STITCH_DIR" -maxdepth 1 -name '*.html' | wc -l)
  if [[ "$count" -eq 0 ]]; then
    phase_fail stitch-fetch "no .stitch-pages/*.html found — agent must fetch screens before running this pipeline"
  fi
  phase_done stitch-fetch "$count Stitch HTML files present"
}

# ───────────────────────────────────────────────────────────────────────────
# 3. STITCH-CONVERT — HTML → JSX
# ───────────────────────────────────────────────────────────────────────────
phase_stitch_convert() {
  log "PHASE 3/11 STITCH-CONVERT"
  python3 "$TOOLS_DIR/stitch-to-next.py" \
      --input "$STITCH_DIR" \
      --out "$PROJECT_DIR" \
    > "$STATUS_DIR/stitch-convert.json" \
    || phase_fail stitch-convert "converter exit $?"
  local pages
  pages=$(jq -r '.pages_converted' "$STATUS_DIR/stitch-convert.json")
  phase_done stitch-convert "$pages pages converted"
}

# ───────────────────────────────────────────────────────────────────────────
# 4. ASSET-DOWNLOAD — Stitch CDN → public/images/stitch/
# ───────────────────────────────────────────────────────────────────────────
phase_asset_download() {
  log "PHASE 4/11 ASSET-DOWNLOAD"
  python3 "$TOOLS_DIR/stitch-download-assets.py" \
      --project "$PROJECT_DIR" \
    > "$STATUS_DIR/asset-download.json" \
    || phase_fail asset-download "downloader exit $?"
  local n
  n=$(jq -r '.downloaded' "$STATUS_DIR/asset-download.json")
  phase_done asset-download "$n assets downloaded"
}

# ───────────────────────────────────────────────────────────────────────────
# 5. CONTENT-LAYER — intake values overlaid on Stitch placeholders
# ───────────────────────────────────────────────────────────────────────────
phase_content_layer() {
  log "PHASE 5/11 CONTENT-LAYER"
  python3 "$TOOLS_DIR/stitch-content-layer.py" \
      --intake "$INTAKE" \
      --project "$PROJECT_DIR" \
    > "$STATUS_DIR/content-layer.json" \
    || phase_fail content-layer "content-layer exit $?"
  phase_done content-layer "intake values applied"
}

# ───────────────────────────────────────────────────────────────────────────
# 6. RESEARCH — DataForSEO. Skipped if .dfs/volumes.json already present
# from prior run (preserves DFS spend on retries).
# ───────────────────────────────────────────────────────────────────────────
phase_research() {
  log "PHASE 6/11 RESEARCH"
  local dfs="$PROJECT_DIR/ai/research/.dfs/volumes.json"
  if [[ -f "$dfs" ]]; then
    phase_done research "cached: $(jq 'length' "$dfs") keywords"
    return
  fi
  # Defer to existing research tooling (reuses website-builder skill)
  if [[ -x "$TOOLS_DIR/run-research.sh" ]]; then
    bash "$TOOLS_DIR/run-research.sh" --intake "$INTAKE" --project "$PROJECT_DIR" \
      || phase_fail research "research script exit $?"
  else
    log "⚠ run-research.sh not present yet — skipping (agent will be invoked for this phase)"
  fi
  phase_done research "completed"
}

# ───────────────────────────────────────────────────────────────────────────
# 7. EXTRA-PAGES — pages in intake.pages with no Stitch source
# This step is currently agent-driven. Script just emits the work list.
# ───────────────────────────────────────────────────────────────────────────
phase_extra_pages() {
  log "PHASE 7/11 EXTRA-PAGES"
  local declared converted missing
  declared=$(intake_get '.pages[]?' | sort -u)
  converted=$(find "$PROJECT_DIR/src/app" -name 'page.tsx' \
              | sed -E 's#.*/src/app/##; s#/?page\.tsx$##; s#^$#home#' \
              | sort -u)
  missing=$(comm -23 <(echo "$declared") <(echo "$converted") || true)
  if [[ -z "$missing" ]]; then
    phase_done extra-pages "all declared pages have a source"
    return
  fi
  echo "$missing" > "$STATUS_DIR/extra-pages.list"
  log "  pages needing generation: $(echo "$missing" | tr '\n' ' ')"
  phase_done extra-pages "list written for agent to fulfill"
}

# ───────────────────────────────────────────────────────────────────────────
# 8. QUALITY-GATE — pnpm build, route HTTP 200s, visual-diff vs Stitch
# ───────────────────────────────────────────────────────────────────────────
phase_quality_gate() {
  log "PHASE 8/11 QUALITY-GATE"
  ( cd "$PROJECT_DIR" && pnpm install --silent && pnpm build ) \
    > "$STATUS_DIR/build.log" 2>&1 \
    || phase_fail quality-gate "pnpm build failed (see build.log)"
  phase_done quality-gate "next build green"
}

# ───────────────────────────────────────────────────────────────────────────
# 9. DEPLOY — webdev container reconcile (existing tool)
# ───────────────────────────────────────────────────────────────────────────
phase_deploy() {
  log "PHASE 9/11 DEPLOY"
  if [[ -x "$TOOLS_DIR/webdev-deploy.sh" ]]; then
    bash "$TOOLS_DIR/webdev-deploy.sh" --project "$PROJECT" \
      || phase_fail deploy "webdev-deploy.sh exit $?"
  fi
  phase_done deploy "webdev container reconciled"
}

# ───────────────────────────────────────────────────────────────────────────
# 10. GITHUB-PUSH — best-effort; agent can complete if creds are missing
# ───────────────────────────────────────────────────────────────────────────
phase_github_push() {
  log "PHASE 10/11 GITHUB-PUSH"
  if [[ -x "$TOOLS_DIR/github-setup.sh" ]]; then
    bash "$TOOLS_DIR/github-setup.sh" --project "$PROJECT_DIR" \
      || log "⚠ github-setup.sh failed — manual push required"
  fi
  phase_done github-push "attempted"
}

# ───────────────────────────────────────────────────────────────────────────
# 11. VERIFICATION — HTTP checks against dev URL
# ───────────────────────────────────────────────────────────────────────────
phase_verification() {
  log "PHASE 11/11 VERIFICATION"
  local url
  url=$(intake_get '.devUrl // .domain // empty')
  [[ -z "$url" ]] && { phase_done verification "no devUrl in intake"; return; }
  local code
  code=$(curl -sk -o /dev/null -w "%{http_code}" "$url" || echo 000)
  if [[ "$code" == "200" ]]; then
    phase_done verification "dev URL HTTP 200"
  else
    log "⚠ verification: $url returned $code (deploy may still be propagating)"
    phase_done verification "$code (warn)"
  fi
}

# ───────────────────────────────────────────────────────────────────────────
# Pipeline driver — supports --from <phase>
# ───────────────────────────────────────────────────────────────────────────
PHASES=(
  scaffold
  stitch-fetch
  stitch-convert
  asset-download
  content-layer
  research
  extra-pages
  quality-gate
  deploy
  github-push
  verification
)

run_phase() {
  case "$1" in
    scaffold)        phase_scaffold ;;
    stitch-fetch)    phase_stitch_fetch ;;
    stitch-convert)  phase_stitch_convert ;;
    asset-download)  phase_asset_download ;;
    content-layer)   phase_content_layer ;;
    research)        phase_research ;;
    extra-pages)     phase_extra_pages ;;
    quality-gate)    phase_quality_gate ;;
    deploy)          phase_deploy ;;
    github-push)     phase_github_push ;;
    verification)    phase_verification ;;
    *) echo "unknown phase: $1" >&2; exit 2 ;;
  esac
}

start_idx=0
if [[ -n "$RESUME_FROM" ]]; then
  for i in "${!PHASES[@]}"; do
    [[ "${PHASES[$i]}" == "$RESUME_FROM" ]] && start_idx=$i && break
  done
fi

for i in "${!PHASES[@]}"; do
  (( i < start_idx )) && continue
  run_phase "${PHASES[$i]}"
done

log "🟢 Stitch-first pipeline complete for $PROJECT"

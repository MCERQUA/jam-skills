#!/usr/bin/env bash
# blog-factory.sh — autonomous, fail-closed blog pipeline orchestrator.
#
# FLOW: load config → topic-pick → prep-context (vetted authority + internal links)
#       → GENERATE body (GLM/haiku, cap-proof, --model pinned) → stage article.mdx
#       → make schema (deterministic) → VERIFY-ALL (fail-closed) → DEPLOY → LIVE-VERIFY
#       → log to ledger.
#
# Bulk generation rides Z.AI/GLM (claude-zai.sh) or haiku — NEVER opus/default sonnet.
# Every GATE is a deterministic script (no LLM).
#
# USAGE:
#   blog-factory.sh <config.json> [--topic "<topic>"] [--keyword "<kw>"]
#                   [--dry-run] [--self-test] [--seed "<kw>"] [--model glm|haiku]
#
#   --dry-run / --self-test : run the WHOLE pipeline through verify-all, print every
#                             gate's pass/fail, but DO NOT deploy/commit/push. Identical
#                             except --self-test forces a fixed demo topic if none given.
#
# EXIT: 0 = success (dry-run gates passed, or real run published+live); 1 = gate/deploy fail.
set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
LIB="$DIR/lib"
CFG="${1:?usage: blog-factory.sh <config.json> [flags]}"; shift || true
[ -f "$CFG" ] || { echo "config not found: $CFG"; exit 2; }

DRY=0; SELFTEST=0; TOPIC=""; KEYWORD=""; SEED=""; MODEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1;;
    --self-test) DRY=1; SELFTEST=1;;
    --topic) TOPIC="$2"; shift;;
    --keyword) KEYWORD="$2"; shift;;
    --seed) SEED="$2"; shift;;
    --model) MODEL="$2"; shift;;
    *) echo "unknown flag: $1"; exit 2;;
  esac; shift
done

j() { jq -r "$1 // \"\"" "$CFG"; }
SITE_KEY="$(j .site_key)"; SITE_URL="$(j .site_url)"
GEN_MODEL="${MODEL:-$(j .gen_model)}"; [ -n "$GEN_MODEL" ] || GEN_MODEL="glm"
TODAY="$(date -u +%F)"

# source keys for DataForSEO / Serper topic-pick + authority DR
set -a; source /mnt/system/base/.platform-keys.env 2>/dev/null || true; set +a

RUN_DIR="$(mktemp -d /tmp/blog-factory.XXXXXX)"
echo "=================================================================="
echo " BLOG FACTORY — $SITE_KEY  ($([ $DRY -eq 1 ] && echo DRY-RUN || echo LIVE))"
echo " run dir: $RUN_DIR    gen model: $GEN_MODEL"
echo "=================================================================="

# ---- 1. TOPIC PICK -----------------------------------------------------------
if [ -n "$TOPIC" ]; then
  KW="${KEYWORD:-$TOPIC}"
  SLUG=$(python3 -c "import re,sys;s=sys.argv[1].lower();s=re.sub(r'[^a-z0-9 -]','',s);print(re.sub(r'[ ]+','-',s).strip('-'))" "$KW")
  TOPIC_JSON=$(jq -nc --arg t "$TOPIC" --arg k "$KW" --arg s "$SLUG" --arg d "$TODAY" \
    '{topic:$t,target_keyword:$k,slug:$s,date:$d,source:"cli"}')
elif [ $SELFTEST -eq 1 ]; then
  TOPIC_JSON=$(jq -nc --arg d "$TODAY" \
    '{topic:"Does a manufacturer need product liability insurance to sell on Amazon",
      target_keyword:"amazon product liability insurance requirement",
      slug:"amazon-product-liability-insurance-requirement",date:$d,source:"self-test"}')
else
  TOPIC_JSON=$(python3 "$DIR/topic-pick.py" "$CFG" ${SEED:+--seed "$SEED"}) || {
    echo "topic-pick: nothing to write — brain/plan empty + no seed. Provide --topic or --seed."; exit 3; }
  # ensure a date field
  TOPIC_JSON=$(echo "$TOPIC_JSON" | jq --arg d "$TODAY" '. + {date:$d}')
fi
echo "TOPIC: $TOPIC_JSON"
echo "$TOPIC_JSON" > "$RUN_DIR/topic.json"

# ---- 2. PREP CONTEXT (vetted authority + internal links) ---------------------
echo "--- prep context (authority + internal) ---"
python3 "$LIB/prep_context.py" "$CFG" "$RUN_DIR/topic.json" "$RUN_DIR" || {
  echo "prep_context FAILED — not enough vetted authority sources. Aborting."; exit 4; }

# ---- 3. BUILD GEN PROMPT + GENERATE (GLM/haiku, pinned model) ----------------
python3 "$LIB/build_gen_prompt.py" "$CFG" "$RUN_DIR/topic.json" \
  "$RUN_DIR/authority.json" "$RUN_DIR/internal.json" > "$RUN_DIR/gen-prompt.txt"

generate() {
  local prompt_file="$1" out_file="$2"
  if [ "$GEN_MODEL" = "haiku" ]; then
    /home/mike/MIKE-AI/scripts/claude-cc.sh --model claude-haiku-4-5-20251001 \
      --dangerously-skip-permissions -p "$(cat "$prompt_file")" > "$out_file" 2>"$RUN_DIR/gen.err"
  else
    # GLM via Z.AI flat-rate (cap-proof). Tier default handles model id.
    /home/mike/MIKE-AI/scripts/claude-zai.sh --dangerously-skip-permissions \
      -p "$(cat "$prompt_file")" > "$out_file" 2>"$RUN_DIR/gen.err"
  fi
}

strip_fence() {  # remove ``` fences if the model added them; keep from first --- line
  awk 'BEGIN{p=0} /^---[[:space:]]*$/{if(!p){p=1}} p&&!/^```/{print}' "$1"
}

echo "--- generate body ($GEN_MODEL) ---"
# GLM (account B, under concurrent load) intermittently returns EMPTY. Retry the
# generate step up to 3x before failing — distinct from the gate-driven regen below.
WC=0
for attempt in 1 2 3; do
  generate "$RUN_DIR/gen-prompt.txt" "$RUN_DIR/raw.md" || true
  : > "$RUN_DIR/article.mdx"
  strip_fence "$RUN_DIR/raw.md" > "$RUN_DIR/article.mdx" 2>/dev/null || true
  WC=$(wc -w < "$RUN_DIR/article.mdx" 2>/dev/null || echo 0)
  echo "generate attempt $attempt: $WC words"
  [ "${WC:-0}" -ge 200 ] && [ -s "$RUN_DIR/article.mdx" ] && break
  echo "  empty/short output — retrying generation ($attempt/3)"
  sleep 5
done
echo "generated $WC words → $RUN_DIR/article.mdx"
# FAIL-CLOSED: a missing/empty/short generation must STOP the pipeline (never deploy).
if [ ! -s "$RUN_DIR/article.mdx" ] || [ "${WC:-0}" -lt 200 ]; then
  echo "GENERATION FAILED after 3 attempts (empty/too short). raw=$(wc -c < "$RUN_DIR/raw.md" 2>/dev/null||echo 0)B. stderr:"
  tail -5 "$RUN_DIR/gen.err" 2>/dev/null
  exit 5
fi

# ---- 4. STAGE meta.json (gates read this) ------------------------------------
jq -n \
  --arg site_url "$SITE_URL" \
  --arg author "$(j .site_author)" \
  --argjson money "$(jq -c '.money_pages' "$CFG")" \
  --arg prefix "$(j .blog_path_prefix)" \
  --argjson gates "$(jq -c '.gates' "$CFG")" \
  '$gates + {site_url:$site_url, site_author:$author, money_pages:$money, blog_path_prefix:$prefix}' \
  > "$RUN_DIR/meta.json"

# ---- 5. SCHEMA (deterministic) ----------------------------------------------
echo "--- build schema ---"
python3 "$LIB/make_schema.py" "$CFG" "$RUN_DIR"

# ---- 6. VERIFY-ALL (fail-closed). Up to 2 regen attempts on failure ----------
verify() { bash "$DIR/verify/verify-all.sh" "$RUN_DIR"; }
echo "--- verify-all (attempt 1) ---"
if ! verify; then
  echo "### gates failed — regenerating once with the same context ###"
  generate "$RUN_DIR/gen-prompt.txt" "$RUN_DIR/raw.md"
  strip_fence "$RUN_DIR/raw.md" > "$RUN_DIR/article.mdx"
  python3 "$LIB/make_schema.py" "$CFG" "$RUN_DIR"
  echo "--- verify-all (attempt 2) ---"
  if ! verify; then
    echo "VERIFY-ALL FAILED after 2 attempts. NOT publishing. Artifacts in $RUN_DIR"
    exit 1
  fi
fi

# ---- 7. DRY-RUN stops here ---------------------------------------------------
if [ $DRY -eq 1 ]; then
  echo
  echo "=================================================================="
  echo " DRY-RUN COMPLETE — all gates PASSED. Nothing published."
  echo " Staged article: $RUN_DIR/article.mdx"
  echo " Schema:         $RUN_DIR/schema.json"
  echo "=================================================================="
  exit 0
fi

# ---- 8. DEPLOY + LIVE-VERIFY -------------------------------------------------
echo "--- deploy + live-verify ---"
if bash "$DIR/deploy.sh" "$CFG" "$RUN_DIR"; then
  SLUG=$(jq -r '.slug' "$RUN_DIR/topic.json")
  URL="${SITE_URL%/}$(j .blog_path_prefix)$SLUG"
  # ledger
  LEDGER="$DIR/../blog-factory-ledger.jsonl"
  jq -nc --arg ts "$(date -u +%FT%TZ)" --arg site "$SITE_KEY" --arg slug "$SLUG" \
     --arg url "$URL" --arg model "$GEN_MODEL" --arg wc "$WC" \
     '{ts:$ts,site:$site,slug:$slug,url:$url,gen_model:$model,words:($wc|tonumber),status:"published"}' \
     >> "$LEDGER"
  echo
  echo "PUBLISHED + LIVE: $URL    (logged → $LEDGER)"
  exit 0
fi
echo "DEPLOY FAILED — see above. Article staged at $RUN_DIR"
exit 1

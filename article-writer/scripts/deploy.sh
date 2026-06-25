#!/usr/bin/env bash
# deploy.sh — publish a VERIFIED staged article to a client's LIVE site via a CLEAN
# CLONE of the canonical GitHub repo (NEVER the live workspace).
#
# WHY clean-clone (2026-06-25 refactor):
#   The old path deployed from /mnt/clients/<tenant>/openclaw/workspace/Websites/<domain>.
#   That workspace has an auto-save/auto-commit system that churns repos CONCURRENTLY and
#   clobbered the blog MDX mid-deploy. Those local repos are also husk-corrupted (wrong
#   origins, multi-site pollution). GitHub MCERQUA/<domain> is the SOURCE OF TRUTH.
#   So we clone fresh into /tmp, apply the article there, push, and VERIFY on GitHub
#   BEFORE the live check. No write ever touches /mnt/clients.
#
# Framework-aware (next-mdx-content | next-slug-record | markdown). Refuses to deploy
# unless verify-all already passed (caller's job) and refuses to push a husk.
#
# Usage:  deploy.sh <config.json> <work_dir>
#   work_dir must contain a verified article.mdx (frontmatter title/description/date/slug)
# Exit:   0 = deployed AND live (HTTP 200 + body match), 1 = failure (nothing past a safe point)
#
# Requires env (load: set -a; . /mnt/system/base/.platform-keys.env; set +a):
#   - gh CLI authenticated (provides HTTPS clone auth + api verify)
#   - NETLIFY_TOKEN (optional, for build-hook discovery/trigger)
set -uo pipefail
CFG="${1:?usage: deploy.sh <config.json> <work_dir>}"
WORK="${2:?usage: deploy.sh <config.json> <work_dir>}"
ART="$WORK/article.mdx"; [ -f "$ART" ] || ART="$WORK/article.md"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

j() { jq -r "$1 // \"\"" "$CFG"; }
BRANCH="$(j .git_branch)"; FW="$(j .framework)"
BLOG_DIR="$(j .blog_dir)"; BLOG_INDEX="$(j .blog_index)"; SITE_URL="$(j .site_url)"
PREFIX="$(j .blog_path_prefix)"; [ -n "$PREFIX" ] || PREFIX="/blog/"
[ -z "$BRANCH" ] && BRANCH="main"
# GitHub repo: prefer explicit config field, else derive from repo_path basename.
GH_REPO="$(j .github_repo)"
if [ -z "$GH_REPO" ]; then
  DOMAIN="$(basename "$(j .repo_path)")"
  [ -n "$DOMAIN" ] || DOMAIN="$(echo "${SITE_URL#http*://}" | sed 's#/.*##')"
  GH_REPO="MCERQUA/${DOMAIN}"
fi
NETLIFY_BUILD_HOOK="$(j .netlify_build_hook)"   # optional explicit hook URL
NETLIFY_SITE="$(j .netlify_site)"               # optional site name for hook discovery

SLUG=$(awk '/^slug:/{gsub(/slug:|"|'"'"'/,""); gsub(/^ +| +$/,""); print; exit}' "$ART")
TITLE=$(awk -F'"' '/^title:/{print $2; exit}' "$ART")
DESC=$(awk -F'"' '/^description:/{print $2; exit}' "$ART")
DATE=$(awk '/^date:/{gsub(/date:|"|'"'"'/,""); gsub(/^ +| +$/,""); print; exit}' "$ART")
[ -n "$SLUG" ] || { echo "deploy: no slug in $ART"; exit 1; }

echo "=== DEPLOY (clean-clone): $SLUG → github.com/$GH_REPO ($FW) ==="

# --- 1. FRESH CLONE of canonical GitHub into /tmp -----------------------------
CLONE_ROOT="/tmp/blogdeploy"
CLONE="$CLONE_ROOT/$(basename "$GH_REPO")"
mkdir -p "$CLONE_ROOT"
rm -rf "$CLONE" 2>/dev/null || true
echo "  cloning https://github.com/$GH_REPO.git → $CLONE"
if command -v gh >/dev/null 2>&1; then
  gh repo clone "$GH_REPO" "$CLONE" -- --depth 1 --branch "$BRANCH" >/dev/null 2>&1 \
    || gh repo clone "$GH_REPO" "$CLONE" >/dev/null 2>&1 \
    || { echo "deploy: clone FAILED ($GH_REPO)"; exit 1; }
else
  git clone --depth 1 --branch "$BRANCH" "https://github.com/$GH_REPO.git" "$CLONE" >/dev/null 2>&1 \
    || git clone "https://github.com/$GH_REPO.git" "$CLONE" >/dev/null 2>&1 \
    || { echo "deploy: clone FAILED ($GH_REPO)"; exit 1; }
fi
cd "$CLONE" || { echo "deploy: clone dir missing"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "deploy: clone not a git repo"; exit 1; }

# --- HUSK GUARD: a fresh clone shouldn't be a husk, but guard anyway -----------
LOCAL_FILES=$(git ls-files | wc -l)
if [ "$LOCAL_FILES" -lt 5 ]; then
  echo "deploy: ABORT — clone has only $LOCAL_FILES tracked files (implausibly small / husk). Refusing."
  exit 1
fi
echo "  clone OK: $LOCAL_FILES tracked files, HEAD $(git rev-parse --short HEAD)"

# --- 2. write the article into the CLONE by framework -------------------------
REL_DEST=""   # path (relative to repo root) of the new MDX, for GitHub verify
case "$FW" in
  next-mdx-content|markdown)
    EXT="mdx"; [ "$FW" = "markdown" ] && EXT="md"
    REL_DEST="$BLOG_DIR/$SLUG.$EXT"
    DEST="$CLONE/$REL_DEST"
    mkdir -p "$(dirname "$DEST")"
    cp "$ART" "$DEST"
    echo "  wrote $REL_DEST"
    # update the posts[] index array (next-mdx-content only)
    if [ "$FW" = "next-mdx-content" ] && [ -n "$BLOG_INDEX" ] && [ -f "$CLONE/$BLOG_INDEX" ]; then
      python3 "$SCRIPT_DIR/lib/update_index.py" "$CLONE/$BLOG_INDEX" \
        --slug "$SLUG" --title "$TITLE" --description "$DESC" --date "$DATE" \
        && echo "  updated index $BLOG_INDEX" \
        || { echo "  WARN: index update failed — post may not list (continuing)"; }
    fi
    ;;
  next-slug-record)
    REL_DEST="$BLOG_INDEX"
    echo "  next-slug-record: appending record to $BLOG_INDEX"
    python3 "$SCRIPT_DIR/lib/update_index.py" "$CLONE/$BLOG_INDEX" \
      --slug "$SLUG" --title "$TITLE" --description "$DESC" --date "$DATE" \
      --record-from "$ART" || { echo "deploy: record insert failed"; exit 1; }
    ;;
  *)
    echo "deploy: unknown framework '$FW'"; exit 1;;
esac

# --- 3. commit + push to canonical GitHub -------------------------------------
git add -A
if git diff --cached --quiet; then
  echo "deploy: nothing staged (post already present on origin?) — skipping commit"
else
  git -c user.name="blog-factory" -c user.email="blog-factory@jam-bot.com" \
    commit -q -m "blog: $TITLE

Auto-published by the JamBot blog factory (article-writer skill).
Slug: $SLUG" || { echo "deploy: commit failed"; exit 1; }
  echo "  committed."
fi

if git push origin "HEAD:$BRANCH" 2>&1 | tail -3; then
  echo "  pushed HEAD -> origin/$BRANCH."
else
  echo "deploy: push failed"; exit 1
fi
PUSHED_SHA="$(git rev-parse HEAD)"

# --- 4. VERIFY the MDX actually landed on GitHub (guard vs silent push fail) ---
echo "=== GITHUB-VERIFY: repos/$GH_REPO/contents/$REL_DEST ==="
gh_ok=0
for i in 1 2 3 4 5; do
  if gh api "repos/$GH_REPO/contents/$REL_DEST?ref=$BRANCH" --jq '.sha' >/dev/null 2>&1; then
    gh_ok=1; echo "  GitHub api 200: $REL_DEST is on origin/$BRANCH."; break
  fi
  echo "  attempt $i: not visible yet on GitHub api — retrying"; sleep 5
done
if [ "$gh_ok" -ne 1 ]; then
  echo "deploy: ABORT — push reported success but $REL_DEST is NOT on GitHub (api != 200). Silent push failure."
  exit 1
fi

# --- 5. trigger Netlify build (webhook can be unreliable) ----------------------
trigger_build_hook() {
  local hook="$1"
  [ -n "$hook" ] || return 1
  local rc
  rc=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d '{}' "$hook" 2>/dev/null)
  echo "  POST build hook → HTTP $rc"
  [ "$rc" = "200" ] || [ "$rc" = "201" ] || [ "$rc" = "204" ]
}
HOOK="$NETLIFY_BUILD_HOOK"
if [ -z "$HOOK" ] && [ -n "${NETLIFY_TOKEN:-}" ]; then
  # discover the site + its first build hook by domain/name
  SITE_NAME="${NETLIFY_SITE:-$(basename "$GH_REPO" | sed 's/\.com$//')}"
  SITE_ID=$(curl -s -H "Authorization: Bearer $NETLIFY_TOKEN" \
    "https://api.netlify.com/api/v1/sites?filter=all&per_page=200" \
    | jq -r --arg d "$(basename "$GH_REPO")" --arg n "$SITE_NAME" \
        '.[] | select((.custom_domain//""|ascii_downcase==($d|ascii_downcase)) or (.name|ascii_downcase==($n|ascii_downcase))) | .id' \
    | head -1)
  if [ -n "$SITE_ID" ]; then
    HOOK_ID=$(curl -s -H "Authorization: Bearer $NETLIFY_TOKEN" \
      "https://api.netlify.com/api/v1/sites/$SITE_ID/build_hooks" \
      | jq -r --arg b "$BRANCH" '[.[] | select(.branch==$b)][0].id // (.[0].id // "")')
    [ -n "$HOOK_ID" ] && HOOK="https://api.netlify.com/build_hooks/$HOOK_ID"
    echo "  discovered netlify site $SITE_ID, build hook: ${HOOK:-<none>}"
  else
    echo "  WARN: could not discover netlify site for $(basename "$GH_REPO") — relying on push webhook"
  fi
fi
if [ -n "$HOOK" ]; then
  echo "=== TRIGGER NETLIFY BUILD ==="
  trigger_build_hook "$HOOK" || echo "  WARN: build-hook trigger non-2xx — relying on push webhook"
else
  echo "  no build hook available — relying on GitHub→Netlify push webhook"
fi

# --- 6. live verify (content-verified, not just status) -----------------------
# NOTE: these sites are STATIC-EXPORT (output:"export"). The blog [slug] route uses
# generateStaticParams() that globs content/blog/*.mdx, so a new MDX gets a static page
# at build time. If a post 404s after a confirmed push+build, the template's
# generateStaticParams is NOT enumerating MDX slugs → that's a TEMPLATE fix, not a
# deploy bug (report it).
URL="${SITE_URL%/}${PREFIX}${SLUG}"
echo "=== LIVE-VERIFY: $URL ==="
NEEDLE="${TITLE:-$SLUG}"
for i in $(seq 1 30); do
  page=$(curl -s -L --max-time 25 "$URL" 2>/dev/null)
  code=$(curl -s -o /dev/null -L --max-time 20 -w "%{http_code}" "$URL" 2>/dev/null)
  has_body=$(printf '%s' "$page" | grep -cF "$NEEDLE" 2>/dev/null || echo 0)
  echo "  attempt $i: HTTP $code  body-match($NEEDLE)=$has_body"
  if [ "$code" = "200" ] && [ "$has_body" -ge 1 ]; then
    idxcode=$(curl -s -L --max-time 20 "${SITE_URL%/}${PREFIX%/}" 2>/dev/null | grep -c "$SLUG")
    echo "  index references slug: $idxcode occurrence(s)"
    echo "  pushed commit: $PUSHED_SHA"
    echo "DEPLOY OK — live + content-verified: $URL"
    rm -rf "$CLONE" 2>/dev/null || true
    exit 0
  fi
  sleep 20
done
echo "deploy: post NOT content-verified live after ~12min ($URL)."
echo "  MDX IS confirmed on GitHub ($GH_REPO:$REL_DEST). If still 404, suspect: Netlify build failed,"
echo "  OR the static-export blog route's generateStaticParams does not enumerate the new MDX slug."
rm -rf "$CLONE" 2>/dev/null || true
exit 1

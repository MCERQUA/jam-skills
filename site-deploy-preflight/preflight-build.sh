#!/usr/bin/env bash
# preflight-build.sh — prove a website builds BEFORE you push it to a deploy branch.
#
# WHY THIS EXISTS (2026-07-24, printguys.ca):
#   An agent pushed a Footer.tsx with a malformed JSX comment straight to the
#   auto-deploying `web-dev` branch. Netlify failed. The project CLAUDE.md already
#   said "run the build first" — but following that advice IN PLACE was broken two ways:
#
#     1. `next build` inside the live repo OVERWRITES .next, which the tenant's
#        webdev dev-server is actively serving  ->  it takes the dev site down.
#        (Evidence: .next.old, .next.old2, .next.old3 littering the repo.)
#     2. The webdev containers run NODE_ENV=development. `next build` under a
#        non-standard NODE_ENV dies with a BOGUS error:
#            "<Html> should not be imported outside of pages/_document"
#            "Export encountered an error on /_error: /404"
#        That failure has NOTHING to do with the agent's change. An agent that ran
#        the gate saw an unrelated red wall, concluded the gate was noise, and
#        pushed anyway. A gate that cries wolf is worse than no gate.
#
#   This script fixes both: it builds a THROWAWAY COPY (live .next untouched) with
#   NODE_ENV forced to production (no phantom failures). Verified against the
#   known-good commit 923fb52 — reproduces Netlify's result exactly.
#
# USAGE
#   bash preflight-build.sh [site-dir]      # defaults to $PWD
#   exit 0 = safe to push     exit 1 = DO NOT PUSH
#
# It never writes to the site directory. It never deletes anything in it.

set -uo pipefail

SITE_DIR="${1:-$PWD}"
SITE_DIR="$(cd "$SITE_DIR" 2>/dev/null && pwd)" || { echo "❌ no such directory: ${1:-$PWD}"; exit 1; }
NAME="$(basename "$SITE_DIR")"
WORK="${TMPDIR:-/tmp}/preflight-${NAME}.$$"

red()  { printf '\033[31m%s\033[0m\n' "$*"; }
grn()  { printf '\033[32m%s\033[0m\n' "$*"; }
info() { printf '  %s\n' "$*"; }

cleanup() { rm -rf "$WORK" 2>/dev/null; }
trap cleanup EXIT

[ -f "$SITE_DIR/package.json" ] || { red "❌ $SITE_DIR has no package.json — not a buildable site."; exit 1; }

if [ ! -d "$SITE_DIR/node_modules" ]; then
    red "❌ $SITE_DIR/node_modules missing."
    info "Install first (store is local, this is fast):  cd $SITE_DIR && pnpm install --prefer-offline"
    exit 1
fi

echo "── preflight build: $NAME ───────────────────────────────"
info "source : $SITE_DIR"
info "sandbox: $WORK   (throwaway — your live .next is NOT touched)"

mkdir -p "$WORK" || { red "❌ cannot create $WORK"; exit 1; }

# Copy source only. node_modules is symlinked (never copied — slow + huge).
# .next is EXCLUDED so we never inherit, and never write back to, the dev server's build.
tar -cf - -C "$SITE_DIR" \
    --exclude=./node_modules --exclude=./.next --exclude='./.next.old*' \
    --exclude=./.git --exclude=./.netlify --exclude=./tmp . 2>/dev/null \
  | (cd "$WORK" && tar -xf -) || { red "❌ failed to stage a copy of the source"; exit 1; }

ln -s "$SITE_DIR/node_modules" "$WORK/node_modules" || { red "❌ could not link node_modules"; exit 1; }

# Pick the package manager the repo actually uses (Netlify picks it from the lockfile too).
PM=npm
[ -f "$SITE_DIR/pnpm-lock.yaml" ] && PM=pnpm
info "pkg mgr: $PM (from lockfile)"

# NODE_ENV=production is THE critical line. See the header comment — without it
# `next build` fails with a phantom <Html>/pages/_document error under the webdev
# container's NODE_ENV=development.
echo "── building (NODE_ENV=production) ───────────────────────"
LOG="$WORK/build.log"
( cd "$WORK" && NODE_ENV=production "$PM" run build ) >"$LOG" 2>&1
STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo
    grn "✅ PREFLIGHT PASSED — this tree builds. Safe to commit + push."
    grep -E "Compiled successfully|Generating static pages|Route \(app\)" "$LOG" | head -3 | sed 's/^/  /'
    exit 0
fi

echo
red "❌ PREFLIGHT FAILED — DO NOT PUSH. Netlify will fail exactly the same way."
echo
echo "── error tail ───────────────────────────────────────────"
# Surface the compile error, not the 200 lines of module trace after it.
grep -nE "Failed to compile|^Error:|error TS[0-9]+|Expected .*, got|Syntax Error|Module not found|Cannot find|ELIFECYCLE" "$LOG" | head -20 | sed 's/^/  /'
echo "─────────────────────────────────────────────────────────"
echo "Full log copied to: /tmp/preflight-${NAME}-FAILED.log"
cp "$LOG" "/tmp/preflight-${NAME}-FAILED.log" 2>/dev/null
echo
echo "Fix the error above, then run this script again. Push only on ✅."
exit 1

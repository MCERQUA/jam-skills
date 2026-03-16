#!/bin/bash
# Website Builder — GitHub Repository Setup
# Creates a private GitHub repo and pushes the scaffold.
#
# Usage: bash github-setup.sh <project-name> [org]
# Example: bash github-setup.sh acme-website MCERQUA
#
# Requires: GITHUB_TOKEN environment variable with repo creation permissions
# The token should be available via platform keys in the container environment.

set -euo pipefail

PROJECT_NAME="${1:?Usage: bash github-setup.sh <project-name> [org]}"
ORG="${2:-MCERQUA}"
WORKSPACE="${3:-/home/node/.openclaw/workspace}"
PROJECT_DIR="$WORKSPACE/Websites/$PROJECT_NAME"

# Verify project exists
if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "ERROR: No git repo found at $PROJECT_DIR"
  echo "Run scaffold.sh first."
  exit 1
fi

# Verify GitHub token
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "ERROR: GITHUB_TOKEN not set."
  echo "Ask admin to add GITHUB_TOKEN to .platform-keys.env"
  exit 1
fi

echo "=== Creating private GitHub repo: $ORG/$PROJECT_NAME ==="

# 1. Create private repo
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "https://api.github.com/orgs/$ORG/repos" \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "{
    \"name\": \"$PROJECT_NAME\",
    \"private\": true,
    \"auto_init\": false,
    \"description\": \"Website for $PROJECT_NAME — built with website-builder skill\"
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "201" ]; then
  echo "ERROR: Failed to create repo (HTTP $HTTP_CODE)"
  echo "$BODY" | head -5
  exit 1
fi

REPO_URL=$(echo "$BODY" | grep -o '"clone_url":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "Repo created: $REPO_URL"

# 2. Add remote and push
cd "$PROJECT_DIR"

# Use token-authenticated URL for push
AUTH_URL="https://$GITHUB_TOKEN@github.com/$ORG/$PROJECT_NAME.git"
git remote add origin "$AUTH_URL" 2>/dev/null || git remote set-url origin "$AUTH_URL"

# Push main branch
git checkout main 2>/dev/null || git checkout -b main
git push -u origin main

# Push web-dev branch
git checkout web-dev
git push -u origin web-dev

# 3. Set web-dev as default working branch (agent always works here)
echo ""
echo "=== GitHub setup complete ==="
echo "Repo: https://github.com/$ORG/$PROJECT_NAME (private)"
echo "Main branch: main (protected — PRs only)"
echo "Working branch: web-dev (agent pushes here)"
echo ""
echo "IMPORTANT: Go to GitHub repo settings and:"
echo "  1. Set web-dev as default branch"
echo "  2. Add branch protection rule for main (require PR)"

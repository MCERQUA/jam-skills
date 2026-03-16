#!/bin/bash
# =============================================================================
# deploy-devsite.sh — Deploy a website project to the JamBot dev server
#
# Run from inside the openclaw container:
#   bash /mnt/shared-skills/website-builder/tools/deploy-devsite.sh <project-name>
#
# This script:
#   1. Validates the project exists and has package.json
#   2. Installs dependencies
#   3. Runs a build to verify it compiles
#   4. Writes .active-project so the webdev container picks it up
#   5. Tells the user to check their dev site URL
#
# The webdev container mounts Websites/ from the same path the agent writes to.
# Files are already shared — this script just ensures deps are installed and
# signals which project should be active.
# =============================================================================

set -e

PROJECT_NAME="${1:-}"
WEBSITES_DIR="/home/node/.openclaw/workspace/Websites"

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: bash deploy-devsite.sh <project-name>"
    echo ""
    echo "Available projects:"
    for dir in "$WEBSITES_DIR"/*/; do
        name=$(basename "$dir")
        if [ -f "$dir/package.json" ]; then
            echo "  $name ($(grep -o '"next"\|"vite"\|"gatsby"\|"nuxt"\|"astro"' "$dir/package.json" | head -1 | tr -d '"'))"
        elif [ -f "$dir/index.html" ]; then
            echo "  $name (static)"
        fi
    done
    exit 1
fi

PROJECT_DIR="$WEBSITES_DIR/$PROJECT_NAME"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project '$PROJECT_NAME' not found in $WEBSITES_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Check if it's a Node project or static site
if [ -f "package.json" ]; then
    echo "[deploy] Project: $PROJECT_NAME (Node.js)"

    # Detect package manager
    if [ -f "pnpm-lock.yaml" ]; then
        PKG="pnpm"
    elif [ -f "yarn.lock" ]; then
        PKG="yarn"
    else
        PKG="npm"
    fi

    # Install deps if needed
    if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
        echo "[deploy] Installing dependencies ($PKG install)..."
        $PKG install
    else
        echo "[deploy] Dependencies already installed"
    fi

    # Build check
    echo "[deploy] Running build check..."
    if $PKG run build 2>&1; then
        echo "[deploy] Build succeeded"
    else
        echo "[deploy] ERROR: Build failed — fix errors before deploying"
        exit 1
    fi
elif [ -f "index.html" ]; then
    echo "[deploy] Project: $PROJECT_NAME (static site)"
else
    echo "ERROR: No package.json or index.html found in $PROJECT_DIR"
    exit 1
fi

# Write active project marker
echo "$PROJECT_NAME" > "$WEBSITES_DIR/.active-project"
echo "[deploy] Set active project to: $PROJECT_NAME"

echo ""
echo "============================================"
echo " DEPLOYED: $PROJECT_NAME"
echo "============================================"
echo ""
echo "The project is ready. The dev server container serves from"
echo "Websites/$PROJECT_NAME/ — files are already shared via bind mount."
echo ""
echo "If the dev server is running a different project, it needs to be"
echo "restarted with WEBDEV_PROJECT_NAME=$PROJECT_NAME."
echo ""
echo "Tell the user to check their dev site URL, or show it in canvas:"
echo "  [CANVAS_URL:https://dev-<user>.jam-bot.com]"
echo ""

#!/bin/bash
# Website Builder — Project Scaffold Script
# Creates a new website project from templates.
#
# Usage: bash scaffold.sh <project-name> [workspace-path]
# Example: bash scaffold.sh acme-website /home/node/.openclaw/workspace
#
# This script:
# 1. Creates project directory in workspace/Websites/
# 2. Copies template files
# 3. Installs dependencies with pnpm
# 4. Initializes git with web-dev branch

set -euo pipefail

PROJECT_NAME="${1:?Usage: bash scaffold.sh <project-name> [workspace-path]}"
WORKSPACE="${2:-/home/node/.openclaw/workspace}"
SKILL_DIR="/mnt/shared-skills/website-builder"
PROJECT_DIR="$WORKSPACE/Websites/$PROJECT_NAME"

# Verify skill exists
if [ ! -d "$SKILL_DIR/templates/project" ]; then
  echo "ERROR: Skill templates not found at $SKILL_DIR/templates/project"
  exit 1
fi

# Check project doesn't already exist
if [ -d "$PROJECT_DIR" ]; then
  echo "ERROR: Project already exists at $PROJECT_DIR"
  exit 1
fi

echo "=== Creating project: $PROJECT_NAME ==="

# 1. Create directory and copy template
mkdir -p "$PROJECT_DIR"
cp -r "$SKILL_DIR/templates/project/"* "$PROJECT_DIR/"
cp "$SKILL_DIR/templates/project/.gitignore" "$PROJECT_DIR/"
cp "$SKILL_DIR/templates/project/.env.local.example" "$PROJECT_DIR/"

# 2. Copy animation wrappers
mkdir -p "$PROJECT_DIR/src/components/animations"
cp "$SKILL_DIR/templates/animations/"*.tsx "$PROJECT_DIR/src/components/animations/"

# 3. Update package.json name
sed -i "s/\"project-name\"/\"$PROJECT_NAME\"/" "$PROJECT_DIR/package.json"

# 4. Create .claude directory with project config
mkdir -p "$PROJECT_DIR/.claude"
cp "$SKILL_DIR/templates/config/claude-project.md" "$PROJECT_DIR/.claude/CLAUDE.md"
sed -i "s/\[PROJECT_NAME\]/$PROJECT_NAME/g" "$PROJECT_DIR/.claude/CLAUDE.md"

# 5. Install dependencies
echo "=== Installing dependencies ==="
cd "$PROJECT_DIR"
if command -v pnpm &> /dev/null; then
  pnpm install --no-frozen-lockfile
else
  npm install
fi

# 6. Initialize shadcn (if CLI available)
echo "=== Initializing shadcn/ui ==="
if command -v pnpm &> /dev/null; then
  pnpm dlx shadcn@latest init -y 2>/dev/null || echo "WARN: shadcn init failed — run manually"
  pnpm dlx shadcn@latest add button card badge separator input textarea label -y 2>/dev/null || echo "WARN: shadcn add failed — run manually"
else
  npx shadcn@latest init -y 2>/dev/null || echo "WARN: shadcn init failed — run manually"
fi

# 7. Initialize git
echo "=== Initializing git ==="
git init
git add -A
git commit -m "feat: scaffold $PROJECT_NAME from website-builder template"
git checkout -b web-dev

echo ""
echo "=== Project scaffolded successfully ==="
echo "Location: $PROJECT_DIR"
echo "Branch: web-dev"
echo ""
echo "Next steps:"
echo "  1. Run github-setup.sh to create private repo"
echo "  2. Fill in .claude/CLAUDE.md with brand info"
echo "  3. Copy section templates from $SKILL_DIR/templates/sections/"
echo "  4. Ask admin to run: sudo bash scripts/jambot-add-website.sh <user> $PROJECT_DIR"

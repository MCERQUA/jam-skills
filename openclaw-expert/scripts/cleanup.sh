#!/bin/bash
# =============================================================
# Hard Cleanup — runs at the 4.5h mark
# Kills ALL remaining build processes, removes cron entries
# =============================================================

BUILD_DIR="/tmp/openclaw-build"
PIDS_DIR="$BUILD_DIR/pids"
WATCHDOG_LOG="$BUILD_DIR/watchdog.log"

echo "$(date): === HARD CLEANUP ===" >> "$WATCHDOG_LOG"

# Kill all remaining agent processes
for pidfile in "$PIDS_DIR"/*.pid; do
    [ -f "$pidfile" ] || continue
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
        echo "$(date): Killing remaining agent PID=$pid ($(basename $pidfile))" >> "$WATCHDOG_LOG"
        kill "$pid" 2>/dev/null
        sleep 1
        kill -9 "$pid" 2>/dev/null
    fi
done

# Also kill any claude processes that might be orphaned from the build
# Only kill those with openclaw-build related args
pkill -f "openclaw-expert/references" 2>/dev/null || true

# Remove ALL cron entries for this build
crontab -l 2>/dev/null | grep -v "openclaw-build" | crontab -

# Generate final index if not done
SKILL_DIR="/home/mike/clawd/skills/openclaw-expert"
if [ ! -f "$SKILL_DIR/index.json" ] || [ "$(stat -c%s "$SKILL_DIR/index.json" 2>/dev/null)" -lt 100 ]; then
    python3 << 'PYEOF'
import json, os
from datetime import datetime
refs_dir = "/home/mike/clawd/skills/openclaw-expert/references"
index = {"version": 1, "generated": datetime.now().isoformat(), "topics": {}, "files": {}, "teaching_modules": []}
for filename in sorted(os.listdir(refs_dir)):
    if not filename.endswith('.md'): continue
    lines = open(os.path.join(refs_dir, filename)).readlines()
    topic_key = filename.replace('.md', '')
    headings = [l.strip().lstrip('#').strip() for l in lines if l.startswith('## ')]
    index["files"][topic_key] = {"file": f"references/{filename}", "lines": len(lines), "headings": headings[:20]}
    index["topics"][topic_key] = {"file": f"references/{filename}", "subtopics": headings[:15]}
with open("/home/mike/clawd/skills/openclaw-expert/index.json", "w") as f:
    json.dump(index, f, indent=2)
PYEOF
fi

# Write final completion marker
REF_COUNT=$(ls "$SKILL_DIR/references/"*.md 2>/dev/null | wc -l)
cat > "$BUILD_DIR/COMPLETE.md" << EOF
# OpenClaw Expert Skill — Build Complete (Hard Cleanup)
- Cleanup time: $(date)
- Reference files: $REF_COUNT/20
- SKILL.md: $(wc -l < "$SKILL_DIR/SKILL.md" 2>/dev/null || echo 0) lines
- index.json: $(stat -c%s "$SKILL_DIR/index.json" 2>/dev/null || echo 0) bytes
- Status: All processes terminated, cron entries removed
EOF

echo "$(date): Hard cleanup complete. $REF_COUNT reference files." >> "$WATCHDOG_LOG"
echo "$(date): All cron entries removed. Pipeline terminated." >> "$WATCHDOG_LOG"

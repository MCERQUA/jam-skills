#!/bin/bash
# =============================================================
# Watchdog — monitors the build pipeline every 15 minutes
# Detects hung agents, restarts them, enforces deadlines
# =============================================================

BUILD_DIR="/tmp/openclaw-build"
LOGS_DIR="$BUILD_DIR/logs"
PIDS_DIR="$BUILD_DIR/pids"
SIZES_DIR="$BUILD_DIR/sizes"
REFS_DIR="/home/mike/clawd/skills/openclaw-expert/references"
SKILL_DIR="/home/mike/clawd/skills/openclaw-expert"
CLAUDE="/home/mike/.local/bin/claude"
CLAUDE_FLAGS="-p --dangerously-skip-permissions --model sonnet --no-session-persistence"

WATCHDOG_LOG="$BUILD_DIR/watchdog.log"

# Check if build is even running
if [ ! -f "$BUILD_DIR/status.log" ]; then
    echo "$(date): No build in progress, exiting" >> "$WATCHDOG_LOG"
    exit 0
fi

# Check if already complete
if [ -f "$BUILD_DIR/COMPLETE.md" ]; then
    echo "$(date): Build already complete, cleaning up cron entries" >> "$WATCHDOG_LOG"
    # Remove our cron entries
    crontab -l 2>/dev/null | grep -v "openclaw-build-watchdog" | grep -v "openclaw-build-cleanup" | crontab -
    exit 0
fi

echo "$(date): === Watchdog check ===" >> "$WATCHDOG_LOG"

# Count running agents
RUNNING=0
HUNG=0
COMPLETED=0

for pidfile in "$PIDS_DIR"/*.pid; do
    [ -f "$pidfile" ] || continue
    name=$(basename "$pidfile" .pid)
    pid=$(cat "$pidfile")
    log="$LOGS_DIR/${name}.log"
    ref="$REFS_DIR/${name}.md"
    sizefile="$SIZES_DIR/${name}.size"

    # Check if output file already exists and has content
    if [ -f "$ref" ] && [ "$(wc -l < "$ref" 2>/dev/null)" -gt 20 ]; then
        COMPLETED=$((COMPLETED + 1))
        continue
    fi

    # Check if process is still running
    if kill -0 "$pid" 2>/dev/null; then
        RUNNING=$((RUNNING + 1))

        # Check if log is growing (compare to last saved size)
        current_size=$(stat -c%s "$log" 2>/dev/null || echo 0)
        last_size=$(cat "$sizefile" 2>/dev/null || echo 0)

        if [ "$current_size" -eq "$last_size" ] && [ "$current_size" -gt 0 ]; then
            # Log hasn't grown since last check — possibly hung
            echo "$(date): HUNG? $name (PID=$pid) — log unchanged at ${current_size}b" >> "$WATCHDOG_LOG"
            HUNG=$((HUNG + 1))

            # Check retry count
            retries=$(cat "$BUILD_DIR/retries-${name}" 2>/dev/null || echo 0)
            if [ "$retries" -lt 2 ]; then
                echo "$(date): Killing hung agent $name (PID=$pid), retry $((retries+1))" >> "$WATCHDOG_LOG"
                kill "$pid" 2>/dev/null
                sleep 2
                kill -9 "$pid" 2>/dev/null

                echo $((retries + 1)) > "$BUILD_DIR/retries-${name}"

                # Restart with shorter budget
                echo "$(date): Restarting $name" >> "$WATCHDOG_LOG"
                PROMPT=$(head -1 "$log" 2>/dev/null || echo "Complete the reference file for $name")
                (
                    env -u CLAUDECODE $CLAUDE $CLAUDE_FLAGS \
                        --system-prompt "You are a documentation extraction agent. Read OpenClaw docs and create a condensed reference file. Max 500 lines. Tables for config. Bullet lists. Preserve code blocks and CLI commands. Write to $REFS_DIR/${name}.md" \
                        "Read OpenClaw docs related to '$name' from /home/mike/clawd/openclaw/docs/ and create a comprehensive reference file. Search the docs directory for relevant files. Write output to $REFS_DIR/${name}.md" \
                        > "$log" 2>&1
                ) &
                new_pid=$!
                echo "$new_pid" > "$pidfile"
                echo "$(date): Restarted $name as PID=$new_pid" >> "$WATCHDOG_LOG"
            else
                echo "$(date): $name exhausted retries, killing permanently" >> "$WATCHDOG_LOG"
                kill "$pid" 2>/dev/null
                kill -9 "$pid" 2>/dev/null
            fi
        fi

        # Save current size for next check
        echo "$current_size" > "$sizefile"
    else
        # Process exited
        if [ -f "$ref" ] && [ "$(wc -l < "$ref" 2>/dev/null)" -gt 5 ]; then
            COMPLETED=$((COMPLETED + 1))
        else
            echo "$(date): $name exited but no output file — check log" >> "$WATCHDOG_LOG"
        fi
    fi
done

# Count reference files
REF_COUNT=$(ls "$REFS_DIR"/*.md 2>/dev/null | wc -l)
echo "$(date): Status: ${RUNNING} running, ${COMPLETED} completed, ${HUNG} possibly hung, ${REF_COUNT} ref files exist" >> "$WATCHDOG_LOG"

# If all done and no agents running, trigger index generation
if [ "$RUNNING" -eq 0 ] && [ "$REF_COUNT" -ge 15 ]; then
    echo "$(date): All agents done! Triggering index generation..." >> "$WATCHDOG_LOG"

    # Generate index.json if it doesn't exist
    if [ ! -f "$SKILL_DIR/index.json" ] || [ "$(stat -c%s "$SKILL_DIR/index.json" 2>/dev/null)" -lt 100 ]; then
        python3 << 'PYEOF'
import json, os
from datetime import datetime

refs_dir = "/home/mike/clawd/skills/openclaw-expert/references"
index = {
    "version": 1,
    "generated": datetime.now().isoformat(),
    "topics": {},
    "files": {},
    "teaching_modules": [
        {"id": "intro", "title": "What is OpenClaw?", "topics": ["architecture"], "slides": 5},
        {"id": "gateway", "title": "The Gateway Deep Dive", "topics": ["gateway-protocol", "gateway-configuration"], "slides": 8},
        {"id": "skills", "title": "Building Skills", "topics": ["skills-system"], "slides": 6},
        {"id": "channels", "title": "Channel Integration", "topics": ["channels-overview", "channels-detail"], "slides": 7},
        {"id": "agent", "title": "Agent Internals", "topics": ["agent-runtime", "sessions-and-context", "memory-system"], "slides": 8},
        {"id": "security", "title": "Security & Operations", "topics": ["security", "automation"], "slides": 5}
    ]
}
for filename in sorted(os.listdir(refs_dir)):
    if not filename.endswith('.md'): continue
    filepath = os.path.join(refs_dir, filename)
    topic_key = filename.replace('.md', '')
    lines = open(filepath).readlines()
    headings = [l.strip().lstrip('#').strip() for l in lines if l.startswith('## ')]
    index["files"][topic_key] = {"file": f"references/{filename}", "lines": len(lines), "headings": headings[:20]}
    index["topics"][topic_key] = {"file": f"references/{filename}", "subtopics": headings[:15]}

with open("/home/mike/clawd/skills/openclaw-expert/index.json", "w") as f:
    json.dump(index, f, indent=2)
print(f"Index: {len(index['files'])} files")
PYEOF
        echo "$(date): Index generated by watchdog" >> "$WATCHDOG_LOG"
    fi
fi

echo "$(date): Watchdog check complete" >> "$WATCHDOG_LOG"

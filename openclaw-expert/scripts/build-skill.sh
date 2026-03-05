#!/bin/bash
# =============================================================
# OpenClaw Expert Skill — Autonomous Build Pipeline
# =============================================================
# Runs unattended for ~4 hours. Launches claude-code agents in
# batches to extract and condense OpenClaw docs into reference files.
# Self-healing via watchdog. Hard cleanup at 4.5h.
# =============================================================

set -euo pipefail

# Paths
SKILL_DIR="/home/mike/clawd/skills/openclaw-expert"
REFS_DIR="$SKILL_DIR/references"
BUILD_DIR="/tmp/openclaw-build"
LOGS_DIR="$BUILD_DIR/logs"
PIDS_DIR="$BUILD_DIR/pids"
SIZES_DIR="$BUILD_DIR/sizes"
DOCS="/home/mike/clawd/openclaw/docs"
SRC="/home/mike/clawd/openclaw/src"
OPENCLAW="/home/mike/clawd/openclaw"
CLAUDE="/home/mike/.local/bin/claude"

# Timing
START_TIME=$(date +%s)
DEADLINE=$((START_TIME + 4 * 3600))       # 4 hours
HARD_STOP=$((START_TIME + 4 * 3600 + 1800)) # 4.5 hours

# Setup
mkdir -p "$REFS_DIR" "$BUILD_DIR" "$LOGS_DIR" "$PIDS_DIR" "$SIZES_DIR"
echo "$(date): Pipeline started. Deadline=$(date -d @$DEADLINE). Hard stop=$(date -d @$HARD_STOP)." > "$BUILD_DIR/status.log"

# Common claude flags for non-interactive extraction
CLAUDE_FLAGS="-p --dangerously-skip-permissions --model sonnet --no-session-persistence"

# Helper: launch a claude agent for a reference file
launch_agent() {
    local filename="$1"
    local prompt="$2"
    local output_file="$REFS_DIR/$filename"
    local log_file="$LOGS_DIR/${filename%.md}.log"
    local pid_file="$PIDS_DIR/${filename%.md}.pid"

    echo "$(date): Launching agent for $filename" >> "$BUILD_DIR/status.log"

    (
        env -u CLAUDECODE $CLAUDE $CLAUDE_FLAGS \
            --system-prompt "You are a documentation extraction agent. Your job is to read OpenClaw source docs and create a condensed, well-organized reference file. Rules: Max 500 lines. Use tables for config fields. Use bullet lists not paragraphs. Preserve all config examples as code blocks. Preserve all CLI commands. Preserve troubleshooting steps verbatim. No fluff, no introductions — just organized knowledge. Write ONLY to the specified output file." \
            "$prompt" \
            > "$log_file" 2>&1
        echo "$(date): Agent for $filename completed (exit=$?)" >> "$BUILD_DIR/status.log"
    ) &
    local pid=$!
    echo "$pid" > "$pid_file"
    echo "$(date): Agent $filename PID=$pid" >> "$BUILD_DIR/status.log"
}

# Helper: check if deadline approaching
time_remaining() {
    echo $(( DEADLINE - $(date +%s) ))
}

# =====================================================
# STAGE 1: Setup skeleton files
# =====================================================
echo "$(date): === STAGE 1: Creating skeleton ===" >> "$BUILD_DIR/status.log"

# Write initial SKILL.md skeleton (will be replaced in Stage 4)
cat > "$SKILL_DIR/SKILL.md" << 'SKILLEOF'
---
name: openclaw-expert
description: Comprehensive guide to OpenClaw architecture, configuration, skills, gateway, memory, and all platform internals. Use for teaching, debugging, and building on OpenClaw.
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
      },
  }
---

# OpenClaw Expert

Comprehensive knowledge base for the OpenClaw personal AI assistant platform.

## Quick Reference

When asked about OpenClaw, read the relevant reference file:

| Topic | File |
|-------|------|
| Architecture & Overview | `{baseDir}/references/architecture-overview.md` |
| Gateway Protocol | `{baseDir}/references/gateway-protocol.md` |
| Gateway Configuration | `{baseDir}/references/gateway-configuration.md` |
| Agent Runtime & Lifecycle | `{baseDir}/references/agent-runtime.md` |
| Sessions & Context | `{baseDir}/references/sessions-and-context.md` |
| Memory System | `{baseDir}/references/memory-system.md` |
| System Prompt Assembly | `{baseDir}/references/system-prompt.md` |
| Skills System | `{baseDir}/references/skills-system.md` |
| Models & Providers | `{baseDir}/references/models-and-providers.md` |
| Channels Overview | `{baseDir}/references/channels-overview.md` |
| Channels Detail | `{baseDir}/references/channels-detail.md` |
| Tools & Exec | `{baseDir}/references/tools-and-exec.md` |
| Automation | `{baseDir}/references/automation.md` |
| Security | `{baseDir}/references/security.md` |
| CLI Reference | `{baseDir}/references/cli-reference.md` |
| Multi-Agent | `{baseDir}/references/multi-agent.md` |
| Canvas & Nodes | `{baseDir}/references/canvas-and-nodes.md` |
| Troubleshooting | `{baseDir}/references/troubleshooting.md` |
| Glossary | `{baseDir}/references/glossary.md` |

## Teaching Mode

When the user asks you to teach or explain OpenClaw topics:
1. Read the relevant reference file(s) from `{baseDir}/references/`
2. Create an HTML slide presentation and show it on the canvas using `canvas-show`
3. Walk through each slide conversationally via voice
4. See `{baseDir}/references/teaching-presentations.md` for HTML templates

## How to Use

- For quick answers: read the specific reference file matching the topic
- For teaching: generate a canvas presentation from the reference material
- For debugging: check troubleshooting.md first, then the relevant subsystem reference
- For configuration: gateway-configuration.md has the full schema
SKILLEOF

echo "$(date): SKILL.md skeleton created" >> "$BUILD_DIR/status.log"

# =====================================================
# STAGE 2: Launch extraction agents in batches
# =====================================================
echo "$(date): === STAGE 2: Launching extraction agents ===" >> "$BUILD_DIR/status.log"

# --- BATCH 1 (6 agents) ---
echo "$(date): --- Batch 1 (6 agents) ---" >> "$BUILD_DIR/status.log"

launch_agent "architecture-overview.md" \
"Read these files and create a condensed architecture reference:
- $OPENCLAW/README.md
- $DOCS/concepts/architecture.md (if exists, or search for architecture docs in $DOCS/concepts/)
- $DOCS/gateway/index.md (if exists)
- $DOCS/start/getting-started.md (if exists)

Cover: What OpenClaw is, component diagram (Gateway, Channels, Agent Runtime, Tools, Skills, Memory), how a message flows end-to-end, node architecture, key directories (~/.openclaw/, workspace, sessions). Write to $REFS_DIR/architecture-overview.md"

launch_agent "gateway-protocol.md" \
"Read these files and create a condensed gateway protocol reference:
- $DOCS/gateway/protocol.md (if exists, search $DOCS/gateway/ for protocol docs)
- $DOCS/gateway/bridge-protocol.md
- $DOCS/gateway/authentication.md
- $DOCS/gateway/discovery.md
- $DOCS/gateway/network-model.md

Cover: Wire protocol (WebSocket JSON frames), handshake sequence, roles (operator/node), request/response pattern, event types, ALL RPC method categories with names, authentication (tokens, device identity, pairing), network model. Write to $REFS_DIR/gateway-protocol.md"

launch_agent "gateway-configuration.md" \
"Read these files and create a condensed configuration reference:
- $DOCS/gateway/configuration.md
- $DOCS/gateway/configuration-reference.md
- Find any configuration-examples files in $DOCS/gateway/

This is the BIGGEST job. Cover: Config file location (~/.openclaw/openclaw.json), how to edit (wizard, CLI, Control UI, direct), hot reload, COMPLETE schema with every top-level section (agents, channels, session, tools, skills, cron, hooks, network, security) showing key fields, types, and defaults as tables. Include copy-paste config examples. Write to $REFS_DIR/gateway-configuration.md"

launch_agent "agent-runtime.md" \
"Read these files and create a condensed agent runtime reference:
- Search $DOCS/concepts/ for files about agents, agent-loop, agent-workspace
- Also check $DOCS/concepts/ for any files about tools, routing

Cover: Agent lifecycle (workspace resolution, model selection, context window, tool attachment, system prompt build, session load, attempt, completion), workspace layout (AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, MEMORY.md, BOOTSTRAP.md), bootstrap injection, built-in tools list, steering while streaming, queue modes. Write to $REFS_DIR/agent-runtime.md"

launch_agent "sessions-and-context.md" \
"Read these files and create a condensed sessions & context reference:
- Search $DOCS/concepts/ for files about sessions, context, compaction, pruning, session-management

Cover: Session management (main session, per-peer, per-channel-peer), context window (what model sees), token accounting, compaction (when/how, memory flush before compaction), context pruning modes (cache-ttl, auto), session persistence (JSONL files), how to inspect (/status, /context). Write to $REFS_DIR/sessions-and-context.md"

launch_agent "skills-system.md" \
"Read these files and create a condensed skills system reference:
- Search $DOCS/ recursively for files about skills, creating-skills, skills-config, clawhub
- Also check $DOCS/concepts/skills.md and $DOCS/tools/

Cover: Skill format (SKILL.md with YAML frontmatter), three locations (bundled, managed, workspace), precedence rules, gating (requires: bins, env, config, os), config overrides, {baseDir} placeholder, creating custom skills step-by-step, ClawHub (install, update, publish), user-invocable vs model-invocable, progressive disclosure pattern. Write to $REFS_DIR/skills-system.md"

# Wait for Batch 1 to settle before starting Batch 2
echo "$(date): Batch 1 launched, waiting 45min before Batch 2..." >> "$BUILD_DIR/status.log"
sleep 2700  # 45 minutes

# --- BATCH 2 (6 agents) ---
echo "$(date): --- Batch 2 (6 agents) ---" >> "$BUILD_DIR/status.log"

launch_agent "memory-system.md" \
"Read these files and create a condensed memory system reference:
- Search $DOCS/concepts/ for files about memory
- Search $DOCS/ for session-management or compaction related docs

Cover: Memory as plain Markdown on disk, daily logs (memory/YYYY-MM-DD.md), long-term (MEMORY.md), when to write vs auto-flush, pre-compaction memory flush, vector memory search (if available), memory configuration, embedding providers. Write to $REFS_DIR/memory-system.md"

launch_agent "system-prompt.md" \
"Read these files and create a condensed system prompt reference:
- Search $DOCS/concepts/ for system-prompt related docs
- Also read $SRC/agents/system-prompt.ts (first 100 lines for section names)

Cover: How system prompt is assembled (all sections: identity, tooling, safety, CLI ref, skills, memory recall, user identity, date/time, reply tags, messaging, TTS, docs, self-update, model aliases, workspace, sandbox), prompt modes (full, minimal, none), bootstrap file injection, skills list injection format, how to inspect with /context. Write to $REFS_DIR/system-prompt.md"

launch_agent "models-and-providers.md" \
"Read these files and create a condensed models & providers reference:
- Search $DOCS/concepts/ for files about models, model-failover, model-providers
- Search $DOCS/providers/ for ALL provider docs (list the directory first)

Cover: Model configuration (agents.defaults.model), ALL providers with key config fields (Anthropic, OpenAI, Z.AI/GLM, Ollama, Groq, Mistral, Gemini, Together, Fireworks, etc.), OAuth vs API keys, model failover (retry chains, fallback), thinking levels, context window sizes, provider-specific notes. Write to $REFS_DIR/models-and-providers.md"

launch_agent "channels-overview.md" \
"Read these files and create a condensed channels overview reference:
- Search $DOCS/channels/ for index, channel-routing, group-messages, groups files
- List $DOCS/channels/ to see all available channel docs

Cover: Channel architecture (provider plugins), DM policies (pairing, allowlist, open, disabled), group policies and mention gating, channel routing to agents, message flow (inbound, processing, outbound), text chunking and streaming, media handling, reply tags, typing indicators. Write to $REFS_DIR/channels-overview.md"

launch_agent "channels-detail.md" \
"Read ALL individual channel docs in $DOCS/channels/ (list the directory first, read each .md file).
Create a per-channel quick reference.

For each channel include: name, setup steps (brief), key config fields, important gotchas/limitations. Channels to cover: WhatsApp, Telegram, Discord, Slack, Signal, iMessage, BlueBubbles, Google Chat, MS Teams, Matrix, WebChat, IRC, LINE, Zalo, Twitch, and any others found. Write to $REFS_DIR/channels-detail.md"

launch_agent "tools-and-exec.md" \
"Read these files and create a condensed tools & exec reference:
- Search $DOCS/tools/ or $DOCS/ for files about exec, browser, elevated, exec-approvals, subagents, slash-commands, reactions
- Search $DOCS/concepts/tools.md

Cover: All built-in tools with descriptions, exec tool (sandbox modes, approvals, elevated mode), browser tool (setup, profiles, actions), slash commands reference, sub-agents, tool policy and gating. Write to $REFS_DIR/tools-and-exec.md"

# Wait for Batch 2 to settle before starting Batch 3
echo "$(date): Batch 2 launched, waiting 45min before Batch 3..." >> "$BUILD_DIR/status.log"
sleep 2700  # 45 minutes

# Check time remaining
REMAINING=$(time_remaining)
echo "$(date): Time remaining: ${REMAINING}s" >> "$BUILD_DIR/status.log"
if [ "$REMAINING" -lt 3600 ]; then
    echo "$(date): WARNING: Less than 1h remaining, accelerating..." >> "$BUILD_DIR/status.log"
fi

# --- BATCH 3 (6 agents) ---
echo "$(date): --- Batch 3 (6 agents) ---" >> "$BUILD_DIR/status.log"

launch_agent "automation.md" \
"Read all files in $DOCS/automation/ and create a condensed automation reference.
Cover: Cron jobs (syntax, config, examples), heartbeat (intervals, prompt, vs cron), webhooks (setup, endpoints, security), hooks (lifecycle hooks), Gmail Pub/Sub integration, auth monitoring. Write to $REFS_DIR/automation.md"

launch_agent "security.md" \
"Read these files and create a condensed security reference:
- Search $DOCS/security/ for all files
- Search $DOCS/gateway/security/ for security docs
- Check $DOCS/gateway/sandboxing.md

Cover: Threat model overview, DM pairing as default, exec sandboxing (Docker containers), tool policy, network security (bind host, tokens), audit with openclaw security audit, secrets management. Write to $REFS_DIR/security.md"

launch_agent "cli-reference.md" \
"Read all files in $DOCS/cli/ and create a condensed CLI reference.
Cover: ALL CLI commands grouped by category (gateway, agent, send, message, config, doctor, health, status, onboard, configure, setup, pairing, update). Include useful flags and examples for each. Write to $REFS_DIR/cli-reference.md"

launch_agent "multi-agent.md" \
"Read these files and create a condensed multi-agent reference:
- Search $DOCS/concepts/ for multi-agent related docs
- Search $DOCS/ for multi-agent or agent routing docs

Cover: Multi-agent setup (agents.list config), per-agent workspaces/models/tools, channel routing to specific agents, shared vs per-agent skills, session isolation. Write to $REFS_DIR/multi-agent.md"

launch_agent "canvas-and-nodes.md" \
"Read these files and create a condensed canvas & nodes reference:
- Search $DOCS/platforms/ for all platform docs (mac, ios, android, linux)
- Search $DOCS/nodes/ or $DOCS/ for node-related docs

Cover: Canvas system (A2UI, push/reset, eval, snapshot), macOS app (menu bar, Voice Wake, Talk Mode), iOS/Android nodes (Canvas, camera, screen record), node connection protocol (role: node), commands exposed by nodes, Linux systemd setup. Write to $REFS_DIR/canvas-and-nodes.md"

launch_agent "troubleshooting.md" \
"Read these files and create a condensed troubleshooting reference:
- $DOCS/start/troubleshooting.md (if exists)
- Search $DOCS/gateway/ for troubleshooting and doctor docs
- Search $DOCS/ for any other troubleshooting docs

Cover: openclaw doctor as first step, common issues by category (gateway won't start, channel won't connect, model errors, auth issues), log reading (openclaw logs), health checks, config validation errors, per-channel troubleshooting tips. Preserve error messages and fix procedures VERBATIM. Write to $REFS_DIR/troubleshooting.md"

# Wait for Batch 3 before final batch
echo "$(date): Batch 3 launched, waiting 60min before Batch 4..." >> "$BUILD_DIR/status.log"
sleep 3600  # 60 minutes

# --- BATCH 4 (3 agents — glossary, teaching, final SKILL.md) ---
echo "$(date): --- Batch 4 (3 agents — finalization) ---" >> "$BUILD_DIR/status.log"

launch_agent "glossary.md" \
"Read ALL .md files in $REFS_DIR/ and create a glossary of key OpenClaw terms.
Each entry: **Term** — one-line definition.
Include at minimum: Gateway, Agent, Session, Workspace, Context, Compaction, Skill, Tool, Channel, Node, Provider, Bootstrap, Heartbeat, Canvas, A2UI, ClawHub, Pi Agent, Context Pruning, Cache TTL, DM Policy, Group Policy, Memory, SOUL.md, IDENTITY.md, TOOLS.md, AGENTS.md, USER.md, MEMORY.md, BOOTSTRAP.md, RPC, Operator, Pairing, Sandbox, Hook, Cron, Webhook.
Write to $REFS_DIR/glossary.md"

launch_agent "teaching-presentations.md" \
"Create an HTML slide presentation template system for the OpenClaw expert skill.
Include:
1. A reusable HTML template with dark theme (#0a0a0a bg), slide navigation (prev/next buttons), progress bar, keyboard support (arrow keys)
2. CSS styles matching the voice app aesthetic (blues, monospace, dark)
3. Six pre-defined teaching module outlines:
   - 'What is OpenClaw?' (5 slides)
   - 'The Gateway Deep Dive' (8 slides)
   - 'Building Skills' (6 slides)
   - 'Channel Integration' (7 slides)
   - 'Agent Internals' (8 slides)
   - 'Security & Operations' (5 slides)
4. Instructions for the agent on how to fill in the template and show it via canvas-show

Write to $REFS_DIR/teaching-presentations.md"

# Final SKILL.md with full content
launch_agent "SKILL-FINAL.md" \
"Read ALL reference files in $REFS_DIR/ (list the directory, read each one).
Then write a comprehensive SKILL.md (max 400 lines) to $SKILL_DIR/SKILL.md that includes:

1. YAML frontmatter: name=openclaw-expert, description, emoji=brain
2. A 'What is OpenClaw' section (10 lines)
3. Architecture mental model paragraph (15 lines)
4. Quick-reference table pointing to all reference files using {baseDir}/references/ paths
5. Teaching mode instructions (how to create canvas presentations, use canvas-show)
6. Top 10 FAQ with brief answers
7. Troubleshooting quick-start
8. Index of all reference files with 1-line descriptions

Make it well-organized and scannable. The agent should be able to answer most basic questions from SKILL.md alone, and know which reference file to read for deeper detail.

Write to $SKILL_DIR/SKILL.md (overwrite the skeleton)"

# =====================================================
# STAGE 3: Wait for completion and validate
# =====================================================
echo "$(date): === Waiting for all agents to complete ===" >> "$BUILD_DIR/status.log"

# Wait up to remaining time for all agents
while [ $(date +%s) -lt $DEADLINE ]; do
    # Check if any agent PIDs are still running
    RUNNING=0
    for pidfile in "$PIDS_DIR"/*.pid; do
        [ -f "$pidfile" ] || continue
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            RUNNING=$((RUNNING + 1))
        fi
    done

    if [ "$RUNNING" -eq 0 ]; then
        echo "$(date): All agents completed!" >> "$BUILD_DIR/status.log"
        break
    fi

    echo "$(date): $RUNNING agents still running, waiting..." >> "$BUILD_DIR/status.log"
    sleep 120  # Check every 2 minutes
done

# =====================================================
# STAGE 4: Generate index.json
# =====================================================
echo "$(date): === STAGE 4: Generating index.json ===" >> "$BUILD_DIR/status.log"

python3 << 'PYEOF'
import json, os, re
from datetime import datetime

refs_dir = "/home/mike/clawd/skills/openclaw-expert/references"
index = {
    "version": 1,
    "generated": datetime.now().isoformat(),
    "openclaw_version": "2026.2.10",
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
    if not filename.endswith('.md'):
        continue
    filepath = os.path.join(refs_dir, filename)
    topic_key = filename.replace('.md', '')
    lines = open(filepath).readlines()
    headings = [l.strip().lstrip('#').strip() for l in lines if l.startswith('## ')]

    index["files"][topic_key] = {
        "file": f"references/{filename}",
        "lines": len(lines),
        "headings": headings[:20],
        "summary": lines[0].strip() if lines else ""
    }
    index["topics"][topic_key] = {
        "file": f"references/{filename}",
        "subtopics": headings[:15]
    }

with open("/home/mike/clawd/skills/openclaw-expert/index.json", "w") as f:
    json.dump(index, f, indent=2)

print(f"Index generated: {len(index['files'])} files, {len(index['topics'])} topics")
PYEOF

echo "$(date): index.json generated" >> "$BUILD_DIR/status.log"

# =====================================================
# STAGE 5: Validation report
# =====================================================
echo "$(date): === STAGE 5: Validation ===" >> "$BUILD_DIR/status.log"

{
    echo "# OpenClaw Expert Skill — Build Report"
    echo "Generated: $(date)"
    echo ""
    echo "## Reference Files"
    echo ""

    EXPECTED_FILES="architecture-overview gateway-protocol gateway-configuration agent-runtime sessions-and-context memory-system system-prompt skills-system models-and-providers channels-overview channels-detail tools-and-exec automation security cli-reference multi-agent canvas-and-nodes troubleshooting glossary teaching-presentations"

    TOTAL=0
    MISSING=0
    TOOSMALL=0

    for name in $EXPECTED_FILES; do
        f="$REFS_DIR/${name}.md"
        if [ -f "$f" ]; then
            lines=$(wc -l < "$f")
            size=$(stat -c%s "$f" 2>/dev/null || echo 0)
            status="OK"
            if [ "$lines" -lt 20 ]; then
                status="TOO SMALL"
                TOOSMALL=$((TOOSMALL + 1))
            fi
            echo "- [x] ${name}.md — ${lines} lines, ${size} bytes — $status"
            TOTAL=$((TOTAL + 1))
        else
            echo "- [ ] ${name}.md — MISSING"
            MISSING=$((MISSING + 1))
        fi
    done

    echo ""
    echo "## Summary"
    echo "- Files present: $TOTAL/20"
    echo "- Missing: $MISSING"
    echo "- Too small: $TOOSMALL"
    echo "- SKILL.md: $(wc -l < "$SKILL_DIR/SKILL.md" 2>/dev/null || echo 0) lines"
    echo "- index.json: $(python3 -c 'import json; d=json.load(open("/home/mike/clawd/skills/openclaw-expert/index.json")); print(len(d["files"]), "files indexed")' 2>/dev/null || echo 'INVALID')"
    echo ""
    echo "## Agent Logs"
    for log in "$LOGS_DIR"/*.log; do
        [ -f "$log" ] || continue
        name=$(basename "$log")
        lines=$(wc -l < "$log")
        echo "- $name: $lines lines"
    done
} > "$BUILD_DIR/validation-report.md"

echo "$(date): Validation report written to $BUILD_DIR/validation-report.md" >> "$BUILD_DIR/status.log"

# =====================================================
# COMPLETION
# =====================================================
echo "$(date): === PIPELINE COMPLETE ===" >> "$BUILD_DIR/status.log"

cat > "$BUILD_DIR/COMPLETE.md" << EOF
# Build Complete
- Started: $(date -d @$START_TIME)
- Finished: $(date)
- Duration: $(( ($(date +%s) - START_TIME) / 60 )) minutes
- Skill dir: $SKILL_DIR
- Validation: $BUILD_DIR/validation-report.md
EOF

echo "$(date): DONE. See $BUILD_DIR/COMPLETE.md" >> "$BUILD_DIR/status.log"

---
name: submesh-control
description: "How to properly spawn, control, and communicate with worker agents in the 4-pane submesh terminal grid. Use before sending any tasks to worker panes."
---

# Sub-Mesh Terminal Control — Correct Workflow

## Pane Map
- `submesh:grid.0` — Manager (you) — never touch
- `submesh:grid.1` — Worker A
- `submesh:grid.2` — Worker B  
- `submesh:grid.3` — Worker C (often Research-Dept)

---

## Step 1 — Always Check Pane State First

Before doing anything, see what's actually running:

```bash
tmux capture-pane -t submesh:grid.1 -p | tail -5
tmux capture-pane -t submesh:grid.2 -p | tail -5
tmux capture-pane -t submesh:grid.3 -p | tail -5
```

**Three possible states:**
1. **Bash shell** (`$` prompt) — claude is NOT running, must start it
2. **Claude running** (shows `❯` or `bypass permissions`) — ready to receive task
3. **Process running** (dev server, long command) — pane is busy, don't use it

---

## Step 2 — Starting Claude in a Bash Pane

```bash
tmux send-keys -t submesh:grid.1 "export AGENT_URI=worker-a@mesh && cd /workspace/Websites/sandblasting-nextjs && claude --dangerously-skip-permissions" Enter
```

**Then wait for it to fully start:**
```bash
sleep 8
tmux capture-pane -t submesh:grid.1 -p | tail -5
# Look for: "bypass permissions on" or the ❯ prompt
# If still showing startup text, wait 5 more seconds and check again
```

Do NOT send the task until you see claude's prompt. If you send early it goes to bash, not claude.

---

## Step 3 — Sending a Task to Running Claude

### For SHORT tasks (under ~200 chars, no special characters):
```bash
tmux send-keys -t submesh:grid.1 "Research the top 5 competitors for sandblasting insurance and save to memory/competitors.json" Enter
```

### For LONG tasks or tasks with `$`, quotes, parentheses:

**CRITICAL:** `tmux send-keys` runs through YOUR shell first. Any `$VAR` in the string gets replaced with YOUR shell's value (usually empty). This silently garbles the message.

**Correct approach — write to file, paste via buffer:**
```bash
# Write task to a temp file (heredoc with quoted delimiter = no interpolation)
cat > /tmp/task-worker-a.txt << 'TASKEOF'
Your full task here.
You can use $DATAFORSEO_LOGIN and other vars freely — they will NOT be interpolated.
AUTH=$(echo -n "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" | base64)
TASKEOF

# Load file into tmux clipboard buffer
tmux load-buffer /tmp/task-worker-a.txt

# Paste it into the worker pane (types it as if the user typed it)
tmux paste-buffer -t submesh:grid.1

# Then submit
tmux send-keys -t submesh:grid.1 "" Enter
```

---

## Step 4 — Verify the Agent is Actually Working

After sending a task, wait 5 seconds and check:
```bash
sleep 5
tmux capture-pane -t submesh:grid.1 -p | tail -15
```

You should see claude thinking/responding. If you see:
- **bash error** → your message went to bash, not claude
- **syntax error** → shell interpolation mangled your message
- **blank / same prompt** → claude didn't receive it, try again

---

## Step 5 — Monitoring Workers Without Interrupting Them

Read-only check (safe to do anytime):
```bash
tmux capture-pane -t submesh:grid.1 -p | tail -30
```

Never send keys while a worker is mid-response — wait for the `❯` prompt to reappear.

---

## Step 6 — Sending a Mid-Run Correction

If a worker is at its `❯` prompt waiting for input, you can course-correct:
```bash
tmux send-keys -t submesh:grid.1 "Focus only on Texas and California, skip other states. Continue." Enter
```

If it's still processing (no prompt visible), wait until it finishes.

---

## Step 7 — Clearing a Worker for Next Phase

```bash
# Send /clear to reset the context
tmux send-keys -t submesh:grid.1 "/clear" Enter
sleep 2
# Then assign the next task
```

---

## Common Mistakes

| Mistake | What Actually Happened | Fix |
|---|---|---|
| Sending task to bash pane | Text was typed into bash, not claude | Start claude first, verify prompt, then send |
| Using `$VAR` in tmux send-keys | Parent shell replaced var with empty string | Write to file, use `tmux load-buffer` + `paste-buffer` |
| Sending task before claude fully starts | Task went to bash during startup | Wait 8-10s, verify `bypass permissions` before sending |
| Sending to a pane running a process | Text queued behind process, never reached claude | Don't use busy panes, use free slots |
| Killing dev server to free a pane | Broke the running preview | Open a new tmux window instead: `tmux new-window -t submesh` |

---

## Opening a New Worker Window (when grid is full)

```bash
tmux new-window -t submesh -n "worker-d"
tmux send-keys -t submesh:worker-d "export AGENT_URI=worker-d@mesh && cd /workspace/Websites/sandblasting-nextjs && claude --dangerously-skip-permissions" Enter
```

Access it: `join-submesh worker-d`

---

## Full Example — Spawning 2 Research Workers

```bash
# 1. Check states
tmux capture-pane -t submesh:grid.2 -p | tail -3
tmux capture-pane -t submesh:grid.3 -p | tail -3

# 2. Start claude in grid.2 (if showing bash)
tmux send-keys -t submesh:grid.2 "export AGENT_URI=worker-b@mesh && cd /workspace/Websites/sandblasting-nextjs && claude --dangerously-skip-permissions" Enter

# 3. Wait for startup
sleep 10
tmux capture-pane -t submesh:grid.2 -p | tail -3
# Confirm: shows "bypass permissions on"

# 4. Write task to file
cat > /tmp/task-b.txt << 'TASKEOF'
Use the Agent tool to run WebSearch for "sandblasting contractor insurance" top 10 results.
For each result document: URL, page title, main sections, CTAs visible.
Save findings to /workspace/Websites/sandblasting-nextjs/ai/research/competitors.json
TASKEOF

# 5. Paste task into worker
tmux load-buffer /tmp/task-b.txt
tmux paste-buffer -t submesh:grid.2
tmux send-keys -t submesh:grid.2 "" Enter

# 6. Verify it's working
sleep 5
tmux capture-pane -t submesh:grid.2 -p | tail -15
```

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

## Step 0 — REVIEW BEFORE YOU DISPATCH (the #1 rule)

**Most wasted worker effort comes from skipping this.** Before you write a single task, spend real time understanding the project — or your workers will produce duplicate, off-system, or wrong-target work that you then throw away.

Checklist before any dispatch:

1. **Find the existing system.** Does the project already have a content pipeline, research dir, templates, build tooling, or conventions? (e.g. `ai/knowledge/`, `ai/research/`, `docs/`, a `build-*.py`, an `AGENTS.md`). Read it. Tell workers to USE it — don't let them reinvent a parallel one.
2. **Check the CANONICAL state, not just your local copy.** `git fetch && git log --oneline origin/<branch> -15`. A stale local checkout hides work that already exists on origin. (Real failure: planned 5 articles off a local checkout; origin already had them — all duplicates.)
3. **Detect existing automation.** Look for cron/daily commits (`blog: …`, `improve(friday): …`, `social: …`). If a job is already maintaining this area, **the submesh is redundant there** — don't compete with it. Surface it to the human instead of duplicating.
4. **Get the real numbers.** If priorities depend on data (keyword volume, metrics), pull REAL data before assigning. Don't let workers estimate — estimates were 20–200× wrong in practice. Confirm API creds are actually loaded (`source` the keys file) before trusting any tool call.
5. **Decide the merge model up front** (see "Shared files" below). If multiple workers would touch the same file, plan staging + manager-merge now, not after they clobber each other.

If you cannot answer "what already exists and who/what already maintains it," you are not ready to dispatch.

---

## Step 0.5 — Write the Shared Contract Before Fan-Out

Before dispatching any workers, write a `BRIEF.md` at the project root containing:
- Data schema (field names, types, example values)
- API surface (endpoint paths, request/response shapes)
- File output paths and port
- Any shared constants (e.g. SHEET_WIDTH, pricing formula)

Workers read `BRIEF.md` as their first instruction. This ensures parallel workers build against a single contract rather than guessing at interfaces.

```bash
cat > /workspace/Websites/my-app/BRIEF.md << 'BRIEFEOF'
# My App — Build Brief
## Stack: Next.js 14, port 3099
## Data schema: { id, title, address, lat, lng, date }
## API: GET/POST /api/items
BRIEFEOF
```

Without a shared contract, workers A–D guess at each other's data shapes and API contracts, causing type mismatches caught only at runtime after all workers complete.

Also add one sentence to `coding-delegation`: "Before fan-out, write a shared `BRIEF.md` (see submesh-control Step 0.5) so parallel workers build against a single data/API contract."

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

**Capture the pane's stable `%id` before proceeding:**
```bash
PANE_A=$(tmux list-panes -a -F '#{pane_index} #{pane_id} #{session_name}:#{window_name}' | awk '/submesh:grid/{print}' | awk 'NR==2{print $2}')
echo "Worker A pane id: $PANE_A"
```
Use `$PANE_A` for all subsequent `paste-buffer`, `send-keys`, and `capture-pane` calls instead of `submesh:grid.1` slot notation. Slot indices shift when you open new windows; `%id` is stable across layout changes.

| Mistake | What Happened | Fix |
|---|---|---|
| Using `grid.N` slot after opening a new tmux window | Grid indices remapped; C-c hit wrong worker | Capture `%id` at start, use it for all subsequent commands |

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

**Read the bottom status line — it tells you the true state:**
- `esc to interrupt` → claude is **processing** your task ✅
- `← for agents` / plain `❯` → claude is **idle** (task NOT running — it didn't submit)
- `Press up to edit queued messages` → your text is **queued**, not yet sent
- `100% context used` → the session is **full** — it will compact/degrade; hard-reset it (Step 7) before tasking

If you see:
- **bash error** → your message went to bash, not claude
- **syntax error** → shell interpolation mangled your message
- **blank / same prompt / idle** → claude didn't receive it, try again

**Paste-submit gotcha:** after `paste-buffer`, a large paste can collapse (`paste again to expand`) and the trailing `send-keys "" Enter` may NOT submit it. If the pane is still idle, send a real Enter: `tmux send-keys -t submesh:grid.1 Enter` and re-verify you see `esc to interrupt`.

**Clear stray input first:** panes often hold leftover unsent text in the input box (a half-typed note, a previous suggestion). Send `tmux send-keys -t submesh:grid.1 C-u` to kill the line before pasting, so it can't accidentally fire or concatenate with your task.

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

## Step 7 — Clearing a Worker for Next Phase (and rescuing a stuck one)

One deliverable per worker session. Between tasks, reset context — and **verify the reset actually happened**:

```bash
tmux send-keys -t submesh:grid.1 C-u           # clear any stray input
tmux send-keys -t submesh:grid.1 "/clear" Enter
sleep 3
tmux capture-pane -t submesh:grid.1 -p | tail -4   # confirm: no "100% context used", clean ❯ prompt
```

**Rescuing a stuck / full-context worker** (pinned at `100% context used`, or a hung command, or `/clear` didn't take):
```bash
tmux send-keys -t submesh:grid.1 Escape        # interrupt whatever it's doing
sleep 1
tmux send-keys -t submesh:grid.1 C-u           # kill the input line
sleep 1
tmux send-keys -t submesh:grid.1 "/clear" Enter
sleep 4
tmux capture-pane -t submesh:grid.1 -p | tail -4   # MUST show fresh prompt, no context %
```
If it still won't reset, restart claude in the pane (Step 2). A worker at 100% context cannot produce a long, high-quality deliverable — reset it before assigning, don't push through.

---

## Common Mistakes

| Mistake | What Actually Happened | Fix |
|---|---|---|
| Sending task to bash pane | Text was typed into bash, not claude | Start claude first, verify prompt, then send |
| Using `$VAR` in tmux send-keys | Parent shell replaced var with empty string | Write to file, use `tmux load-buffer` + `paste-buffer` |
| Sending task before claude fully starts | Task went to bash during startup | Wait 8-10s, verify `bypass permissions` before sending |
| Sending to a pane running a process | Text queued behind process, never reached claude | Don't use busy panes, use free slots |
| Killing dev server to free a pane | Broke the running preview | Open a new tmux window instead: `tmux new-window -t submesh` |
| **Dispatching before reviewing the project** | Workers wrote off-system / duplicate / wrong-target content | Do **Step 0** first — read the existing system, check origin, detect automation |
| **Trusting the worker's DONE report** | Worker claimed "all links verified"; 3 were 404s, image was missing, excerpt over limit | **Verification Gate** (below): re-check every claim yourself |
| **Working off a stale local checkout** | Local had 46 articles; origin had 58 + an active cron → wrote duplicates | `git fetch`; diff against `origin/<branch>` before planning |
| **Multiple workers editing one shared file** | Concurrent edits to `articles.ts` would clobber each other | **Stage-and-merge**: workers write separate files; manager merges |
| **Trusting estimated metrics** | Worker "keyword volumes" were 20–200× wrong (no API creds in its shell) | Pull REAL data; confirm creds are `source`d first |
| **`/clear` assumed to work** | Pane stayed at 100% context; new task queued behind a degraded session | Verify the reset (Step 7); hard-reset if needed |
| **Paste didn't submit** | Collapsed paste; `"" Enter` no-op; task never started | Send real `Enter`; confirm `esc to interrupt` |
| **Trusting `submesh-agents` status** | Showed workers "stopped" while they were actively processing | Verify real state via `tmux capture-pane`, not the status table |

---

## The Verification Gate — NEVER trust a worker's self-report

Workers will confidently report "✅ all checks pass" while shipping broken work. **You are the quality gate. Re-verify every objective claim yourself** before accepting or merging:

- **Links resolve** — grep the output for every link; check each target actually exists (valid route slugs / real files). Don't accept "verified against app/" — verify it.
- **Schema/JSON is valid** — parse it (`python3 -c "import json; json.load(...)"`).
- **It builds** — run the real build in the **main checkout** (which has `node_modules`); a fresh worktree will fail at `install`.
- **Numbers are real** — word count, title/meta length, volumes. Re-measure.
- **No fabricated facts** — spot-check any precise stat against a cited source.

Fix small deterministic defects yourself (a wrong link, an over-long excerpt); bounce larger ones back to the worker with the exact correction. Real defects caught this way every run: broken `/services/` slugs, wrong `/blog/<cat>/<slug>` URL format, missing featured images, duplicate articles. Self-reports said all of these "passed."

---

## Shared files — stage-and-merge, never concurrent-edit

If two or more workers would write to the **same file** (a generated `articles.ts`, a shared registry, one config), do NOT let them edit it directly — they'll overwrite each other (last-write-wins / auto-save collisions).

Pattern:
1. Each worker writes its output to a **separate staging file** (`ai/research/new-articles/<slug>.json`).
2. The **manager reviews each**, then **merges sequentially** into the shared file in one controlled edit.
3. De-dup at merge time (check the slug/key isn't already present on origin — the cron may have added it).

---

## Pushing safely — isolated worktree off origin

The submesh shares ONE working checkout, often with an auto-save committer and/or a cron writing to the same branch. **Never `git checkout <branch>` in the shared checkout to push** — you'll disrupt the workers and fight the cron. Instead:

```bash
git fetch origin -q
git worktree add -b push/<topic> /tmp/push origin/<target-branch>   # isolated, off latest origin
# copy ONLY the verified files into /tmp/push, commit, secret-scan, then:
git push -u origin push/<topic>        # push a feature branch → request PR (direct main push is often hook-blocked)
git worktree remove /tmp/push --force
```
Build-verify in the **main checkout** (has deps), not the worktree. Confirm origin didn't change the same files since your fork point (`git diff <base> origin/<branch> -- <file>`).

---

## Validated — Self-Test Harness

This workflow was tested end-to-end (2026-05-31) against a sandbox catalog project, exercising every discipline above. **7/7 gates passed**, including a negative case (the verification gate correctly rejected a planted duplicate + broken-link file). To re-validate after edits, build a throwaway project with: a shared data file, a `ROUTES.txt` (valid-link allowlist), a `PLAN.md` with some already-built + some new items (dedup target), and a local bare-repo `origin` (push target). Then run the full loop — review → reset+verify → dispatch+verify-submit → independent verification gate (positive AND negative) → stage-and-merge → worktree push — and confirm each gate fires. If any gate can't be demonstrated, the procedure (or your tooling) is broken; fix before relying on it.

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

---

## See also

- **agent-git-push-workflow** — how dispatched worker agents push their completed work to MCERQUA canonical repos using SSH deploy keys. Load this skill when wiring the final push step of any worker build.

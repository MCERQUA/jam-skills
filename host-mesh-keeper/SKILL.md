---
name: host-mesh-keeper
description: "host@mesh always-on pattern — Claude Code session persists via tmux + optional systemd user unit so mesh agents can reach host independent of Mike's terminal session. Covers lifecycle (start/attach/detach/stop), behavior rules (when tmux-backed host acts autonomously vs waits), and troubleshooting. Trigger: 'host always on', 'tmux host', 'persistent host', 'mesh-keeper', 'host crashed'."
---

# host-mesh-keeper

**The problem:** mesh agents write to `/mnt/agent-mesh/agents/host/inbox/`. If there's no Claude Code session actively listening, those files sit unread until Mike next opens a terminal. Agents expecting a reply hang. host@mesh becomes a part-time node instead of always-on infrastructure.

**The fix:** `scripts/host-mesh-keeper.sh` runs Claude Code inside a detached tmux session named `host-mesh`, pre-armed with `/mesh-start` so the inbox Monitor is live. tmux keeps the session alive across Mike's SSH disconnects. Optional systemd user unit restarts on crash + auto-launches on reboot.

## Lifecycle

```bash
# Start (or attach to existing)
bash scripts/host-mesh-keeper.sh start

# Watch it work (read-only) or interact
tmux attach -t host-mesh
# Detach without stopping: Ctrl-b d

# Check state
bash scripts/host-mesh-keeper.sh status

# Tail the session log (useful when not attached)
bash scripts/host-mesh-keeper.sh logs

# Clean shutdown
bash scripts/host-mesh-keeper.sh stop

# Restart (e.g. after pulling a new claude binary)
bash scripts/host-mesh-keeper.sh restart
```

Session name: `host-mesh`. Log file: `/tmp/host-mesh-keeper.log` (tmux pane pipe).

## Optional: systemd user unit (survive reboots)

```bash
bash scripts/install-host-mesh-keeper.sh
# Enable auto-start even when mike not logged in:
sudo loginctl enable-linger mike
systemctl --user enable --now host-mesh-keeper.service
```

Unit restarts on crash (rate-limited 3/10min). Disable with
`systemctl --user disable --now host-mesh-keeper.service`.

## Behavior rules — tmux-backed vs ephemeral

When host@mesh runs in tmux (always-on mode), behavior shifts slightly vs an ephemeral session:

| Situation | Ephemeral host | Tmux-backed host |
|---|---|---|
| Agent sends routine mesh msg | Waits until Mike runs `claude` | Processes within seconds (Monitor event fires) |
| Agent reports blocker | Mike sees next time he opens terminal | Host surfaces via agent mesh reply immediately |
| Mike redirects mid-task | Mike is there to redirect | Host acts on its own orchestrator-skill rules |
| Decision required from Mike | Mike decides next session | Host surfaces via mesh message labeled DECISION NEEDED |

**Implication:** tmux-backed host should follow `mesh-orchestrator` + `feedback_silent_mesh_processing` rules STRICTLY. Mike isn't watching most of the time, so spurious "ok acking now" chatter goes unseen → buildup of noise inside the tmux pane that a future attach finds overwhelming.

## What tmux-backed host SHOULD do autonomously

- Process routine mesh acks + peer replies (use silent-mesh rule)
- Apply `mesh-orchestrator` conductor pattern for multi-agent rollouts
- Commit + push its own work to canonical repos (it has full gh CLI auth on host)
- Update registry entries when agents report role changes
- File follow-up memories for blocked/deferred work

## What tmux-backed host SHOULD NOT do autonomously

- Run `sudo` anything — Mike does not have passwordless sudo; never attempt
- Spend money (paid API calls beyond routine agent replies) without Mike ack
- Rebuild/restart Docker containers that might interrupt Mike's active work
- Delete, force-push, or otherwise destructive ops
- Expose ports or change firewall rules
- Send external messages (email/Slack/SMS to anyone not on mesh)

If it can't proceed without one of these, surface a DECISION message to Mike via direct mesh (he sees `/mnt/agent-mesh/agents/host/sent/` when attached).

## Troubleshooting

**Session won't start: "claude binary not found"**
- `CLAUDE_BIN` override: `CLAUDE_BIN=/path/to/claude bash scripts/host-mesh-keeper.sh start`
- Default path: `/home/mike/.local/bin/claude`

**Session died silently**
- Check `/tmp/host-mesh-keeper.log` for the last output before death
- Usually: auth expired, API rate-limited, model deprecated
- `systemctl --user status host-mesh-keeper.service` if using systemd

**`/mesh-start` didn't fire**
- The 5-second sleep between `claude` launch + `/mesh-start` may be too short
  on slow boot. Attach, run `/mesh-start` manually. If it's consistently slow,
  increase the `sleep 5` in the keeper script.

**Multiple sessions with same name**
- tmux allows only one `host-mesh`. If `start` says "already running",
  either attach to the existing or `stop` first.

**Mike's tmux sessions conflict**
- Unlikely but if Mike uses tmux for other purposes, session name
  `host-mesh` is reserved. Don't name other sessions that.

## What attach looks like

Attaching shows:
1. Banner output from start (`=== host-mesh keeper started ...`)
2. Claude Code prompt
3. Monitor events streaming as mesh files arrive + host responses

Useful commands inside the attached session:
- `/usage` — token spend summary
- `/status` — session info
- `/memory` — what's loaded
- Type directly to give host@mesh a new task

Detach with `Ctrl-b d`. Host continues running.

## When to use ephemeral mode instead

Don't run the keeper during:
- Active development on the bridge / mesh-send / mesh-recv themselves (you
  need to see each change land + react; keeper hides the loop)
- Cost-sensitive experiments (a tmux-backed host may process a test mesh
  blast you didn't mean to trigger autonomously)
- First time testing a new skill (you want to see each step)

Stop the keeper, use ephemeral `claude` directly, restart when done.

## Cross-refs

- `mesh-orchestrator` — how host conducts multi-agent work (tmux-backed amplifies this)
- `feedback_silent_mesh_processing` — noise rule especially important when Mike isn't watching
- `feedback_all_sessions_are_you` — tmux-backed host owns its work, commits, pushes
- `/mnt/agent-mesh/mesh/PROTOCOL.md` — mesh v2.0.1

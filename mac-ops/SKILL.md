---
name: mac-ops
description: "Operational rules for managing macOS mesh nodes — systemd/launchd process ownership, VNC session stability, diagnostic order, and Mac UI automation defaults. Read before touching any Mac service, process, or desktop UI."
version: 1.0.0
---

# Mac Ops — Rules for macOS Mesh Nodes

Operational rules derived from real incidents. Each rule has a cost if ignored.

---

## Rule 1: `systemctl status` BEFORE touching any process

**Always run `systemctl status <service>` (on VPS) or `launchctl list <label>` (on Mac) before killing, restarting, or nohup-ing any process.**

```bash
# On VPS — check a service before touching it
sudo systemctl status novnc-macdaddy-shim

# On Mac — check a launchd job before touching it
launchctl list com.jambot.mac-listener
```

**Why:** If a service is already managed, your manual process will compete for the same port/socket. The systemd-managed service will restart on a schedule and kill your manual copy, or vice versa — causing crash-loops that drop dependent connections (VNC sessions, websocket tunnels, etc.).

**Incident:** 978 crash-loops of `novnc-macdaddy-shim.service` caused by a `nohup` instance holding port 5901. Every loop dropped active VNC sessions. 90 min debugging time. `systemctl status` at the start would have shown the conflict in 5 seconds.

---

## Rule 2: Single owner per port — never mix systemd and manual

If a service is in a systemd unit file, **only systemd manages it.** Never:
- `nohup python3 service.py &`
- `./start.sh &`
- Add a crontab watchdog that restarts it

Do:
```bash
sudo systemctl restart <service>   # restart
sudo systemctl stop <service>      # stop
sudo systemctl start <service>     # start
journalctl -u <service> -n 50      # logs
```

**Corollary:** If you need to test a config change, edit the unit file or the script it calls, then `sudo systemctl restart`. Never run the binary directly.

---

## Rule 3: VNC session stability — what protects it and what kills it

**What keeps VNC alive:**
- `caffeinate -dis` (launchd job `com.jambot.caffeinate-display`) — prevents display sleep + idle sleep
- `idle-wiggle` (launchd job, 45s interval) — resets idle timers
- TCP keepalive on rfb-type2-shim — prevents NAT from silently dropping idle connections
- Session watchdog (`com.jambot.session-watchdog`, 30s) — detects Dock absence and triggers `killall loginwindow` → auto-login

**What kills VNC:**
- Concurrent AX calls (multiple Peekaboo + osascript calls simultaneously) → AXVisualSupportAgent overload → ScreensharingAgent crash
- Manual nohup instance on port 5901 competing with systemd shim → crash-loop → repeated TCP resets
- Display sleep — lock screen appears, Secure Input blocks keyboard, user can't retype password

**Gate rule:** Serialize Peekaboo calls. Do not run multiple `peekaboo see` or `osascript` AX commands concurrently.

---

## Rule 4: Mac UI automation — Peekaboo element IDs are the default

See `peekaboo-click-patterns` skill for full details.

Short version:
1. `peekaboo see` — get AX tree with element IDs
2. Find your target by role + label
3. `peekaboo click --on elem_N`

**Never** start with `osascript` or pyautogui coordinates. Those are fallbacks for when AX is unavailable (canvas/game UIs), not defaults.

---

## Rule 5: Lock screen = hard stop

macOS 26 Secure Input blocks **all** VNC keyboard events at the kernel level when the lock screen or a password field has focus. There is no software workaround from the VPS side.

**Prevention is the only fix:**
- Ensure `caffeinate -dis` is running
- Ensure `idle-wiggle` is running
- Ensure the session watchdog auto-logins if the Dock disappears

If prevention fails and the screen is locked, the session watchdog will detect the missing Dock within 30s and fire `killall loginwindow` → auto-login restores VNC access.

---

## Rule 6: `/dev/console owner = root` is not a session loss signal

On headless Macs, `stat /dev/console` shows `root` even during a healthy session. Do not use this as a health check. Use:

```bash
pgrep -u macdaddy Dock   # non-zero = session alive
```

---

## Services reference (Mac Mini — macmini-office@mesh)

| Label | What it does | Manage with |
|---|---|---|
| `com.jambot.mesh-heartbeat` | Writes liveness every 60s | `launchctl` |
| `com.jambot.mac-listener` | Routes mesh inbox → handlers | `launchctl` |
| `com.jambot.canvas-kiosk` | Chrome kiosk to canvas URL | `launchctl` |
| `com.jambot.caffeinate-display` | `caffeinate -dis` forever | `launchctl` |
| `com.jambot.idle-wiggle` | Resets idle timers every 45s | `launchctl` |
| `com.jambot.session-watchdog` | Detects Dock loss, fires loginwindow reset | `launchctl` (root daemon) |

## Services reference (VPS — novnc stack)

| Unit | What it does | Manage with |
|---|---|---|
| `novnc-macdaddy-shim.service` | rfb-type2-shim on :5901 | `sudo systemctl` |
| `websockify` (unit name TBD) | websockify on :6090 | `sudo systemctl` |

Logs: `~/Library/Logs/jambot/` (Mac), `journalctl -u <unit>` (VPS).

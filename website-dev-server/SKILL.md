---
name: website-dev-server
description: Manage multi-website dev environments where only ONE site is "hot" (live dev server) at a time. Covers switching protocol, canvas preview rules, parked-vs-hot editing, and the never-use-Docker-IPs constraint. Read when the user asks to work on, show, or switch websites.
---

# Website Dev Server

You manage multiple websites. Only **ONE** website can be "hot" (live dev server running) at a time.

The hot site has instant hot-reload when you edit files. Parked sites can still be read/browsed but not live-previewed.

## Showing the HOT website in canvas

**ALWAYS use this exact tag to show the currently hot dev site:**

```
[CANVAS_URL:https://dev-<tenant>.jam-bot.com]
```

Fallback: `[CANVAS_URL:https://<tenant>.jam-bot.com/devsite-<project-name>/]`

**NEVER use Docker internal IPs** (`172.x.x.x`, `localhost`, `10.x.x.x`) — the browser cannot reach them.

You can ONLY preview the HOT website in canvas. If the user asks to see a parked site, you must switch first.

## Editing files

- **HOT site:** Edit files in the project directory — dev server hot-reloads automatically, changes visible instantly in canvas.
- **Parked sites:** You CAN still read and edit files in parked site directories. Changes are saved but won't be visible until that site is switched to hot.

## Switching Protocol — Follow EXACTLY

**Only one site can be hot at a time.** When the user asks to work on a different website, or you need to show a parked site:

### Step 1 — Confirm with the user BEFORE switching

Say something like:
> "Your [CURRENT SITE] website is currently loaded and active. To work on [REQUESTED SITE], I need to switch — this takes about 30 seconds. Are you finished with [CURRENT SITE] for now? Any last changes before I switch?"

### Step 2 — Wait for user confirmation

**Do NOT switch without explicit approval.**

### Step 3 — Execute the switch

```bash
exec("sudo bash /root/MIKE-AI/scripts/jambot-switch-website.sh <tenant> <new-project-name> --park-others")
```

### Step 4 — Confirm completion and show the site

> "All set — [NEW SITE] is now hot and ready. Here it is. [CANVAS_URL:https://dev-<tenant>.jam-bot.com]"

## Rules

- NEVER switch without asking the user first
- NEVER try to run two hot sites simultaneously
- If the user just wants to READ a parked site's code (not preview it), you can do that without switching
- If the user asks to "show" or "pull up" a parked site, that requires a switch
- The list of available websites is in `AGENTS.md` or by listing `workspace/Websites/`

## Listing current websites

```bash
exec("ls -la /home/node/.openclaw/workspace/Websites/")
```

To find the currently hot project, check `.active-project` file in the workspace root.

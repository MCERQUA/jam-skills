---
name: threejs-office-environment
description: Build and extend 3D office/workspace environments as canvas pages with Three.js. Use when creating or modifying interactive 3D offices, rooms, or workspaces that include desks, monitors, TVs, screen sharing, chat, and multiplayer. Also use when adding screen share to any 3D surface, implementing canvas-based multiplayer chat, or building click-drag camera controls for iframe environments.
---

# Three.js Office Environment

Build interactive 3D office spaces as self-contained canvas pages with screen sharing, multiplayer chat, and click-drag camera controls.

## Prerequisites

Read these skills for foundational patterns:
- **threejs-canvas-integration** — import maps, canvas page boilerplate, postMessage API
- **canvas-pages** — page creation, verification, public/private toggling
- **canvas-web-design** — premium CSS for HUD overlays (glassmorphism, dark theme)

## Core Rules (Canvas Iframe Constraints)

These rules apply to EVERY canvas page build. Do not re-discover them.

1. **No CDN except jsdelivr** — unpkg, cdnjs, tailwindcss CDN all silently fail in sandboxed iframes
2. **No pointer lock API** — doesn't work in iframes. Use click-drag camera controls
3. **localhost doesn't resolve** — can't serve local assets. Everything must be self-contained or use jsdelivr URLs
4. **Socket.io from jsdelivr only** — `https://cdn.jsdelivr.net/npm/socket.io-client@4.7.2/dist/socket.io.min.js`
5. **All CSS/JS inline** — no external stylesheets or script files
6. **Google Fonts @import** inside `<style>` tag is OK (graceful fallback if blocked)

## Three.js Setup

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }
}
</script>
```

Socket.io script tag goes BEFORE the importmap (importmap must precede module scripts):
```html
<script src="https://cdn.jsdelivr.net/npm/socket.io-client@4.7.2/dist/socket.io.min.js"></script>
<script type="importmap">...</script>
```

## Click-Drag Camera (Iframe-Safe)

Pointer lock doesn't work in iframes. Use mousedown/mousemove/mouseup instead:

- On mousedown: record position, lock look controls
- On mousemove while down: rotate camera based on delta
- On mouseup: release controls; if distance < 5px from mousedown, treat as click (for object interaction)
- WASD for movement, scroll for zoom

## Screen Share via CanvasTexture

Pattern for showing live content on any 3D surface:

1. Create hidden 2D canvas + context
2. Create `THREE.CanvasTexture(canvas2d)` + `MeshBasicMaterial({ map: texture })`
3. Apply material to a `PlaneGeometry` positioned slightly in front of the display surface
4. On `getDisplayMedia` success: draw video frames to canvas2d via `requestAnimationFrame` loop, set `texture.needsUpdate = true`
5. On stop: revert to idle animation
6. Each screen needs its own canvas, texture, stream, and video variables (fully independent)

See [references/screen-share-pattern.md](references/screen-share-pattern.md) for the complete code pattern.

## Multiplayer Chat & User List

See [references/multiplayer-chat-pattern.md](references/multiplayer-chat-pattern.md) for:
- Welcome dialog with username entry + localStorage persistence
- Socket.io connection to signaling server
- Chat box with message history, Enter-to-send, 50-msg cap
- User list panel with clickable name editing
- Server event handlers (world-state, user-joined/left, chat-message, user-name-changed)

## Signaling Server

- **Server**: `https://dev-test-dev.jam-bot.com`
- **Source reference**: `~/Websites/3D-threejs-site/index.html` (213KB, full multiplayer 3D site)
- **Server code**: `~/Websites/3D-threejs-site/signaling-server.js`
- **Socket events**: user-spawn, chat-message, user-name-change, world-state, user-joined, user-left, user-count-update

Read the source file for detailed event payloads — use grep to find specific handlers:
- Chat display: `grep -n "displayChatMessage\|sendChatMessage" index.html`
- User list: `grep -n "updateUserList\|editUserName" index.html`
- Socket init: `grep -n "socket.on('connect'\|socket.on('world-state" index.html`

## Office Furniture Patterns

Common procedural geometry for office scenes:

- **Desks**: BoxGeometry desktop (2.8 x 0.06 x 1.4) on 4 cylindrical legs
- **Monitors**: BoxGeometry frame (1.2-1.4 x 0.7-0.8 x 0.04) + PlaneGeometry screen + stand/base
- **Chairs**: Seat + back (cushion material), center pole, 5-leg star base
- **TV**: Large BoxGeometry frame on wall, PlaneGeometry screen with thin bezel

All monitors/TVs can have CanvasTexture screens for screen sharing — see references.

## Dark Theme HUD Style

```css
background: rgba(0,0,0,0.7);
backdrop-filter: blur(10px);
border: 1px solid rgba(255,255,255,0.15);
border-radius: 12px;
color: #e2e8f0;
```

Buttons: `background: rgba(59,130,246,0.8)`, same border pattern. z-index 200+ for HUD, 210+ for overlays.

## Workflow Tips

- **Don't split research and action across turns** — context compaction eats your work. Read code and delegate to sub-agent in the same response
- **Sub-agents for edits over ~50 lines** — main session has time constraints
- **Surgical edits, not full rewrites** — use edit tool to target specific lines
- **Verify after sub-agent** — check the file was modified correctly before confirming to user

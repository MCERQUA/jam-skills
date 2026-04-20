---
name: threejs-html-surfaces
description: Paint live, interactive HTML (canvas pages, DOM widgets, videos, iframes) onto NAMED meshes in a Three.js scene. Call out a mesh/object by name (e.g. "tv_screen", "east_wall", "desk_tablet") and mount any canvas page URL or inline HTML onto it — buttons, inputs, sliders, video all stay functional. Declarative API via /pages/_shared/html-surfaces.js. Load after threejs-canvas-integration.
---

# Three.js HTML Surfaces — Declarative "paint canvas page X onto mesh Y"

**The agent ergonomic:** point at a named mesh/object in a 3D scene and say "put this canvas page there." A runtime module does the rest (layout, WebGL upload, pointer → UV → DOM event routing, fallback handling).

```javascript
import * as THREE from "three";
import { mountHtmlSurfaces } from "/pages/_shared/html-surfaces.js";

const surfaces = mountHtmlSurfaces({
  scene, camera, renderer,
  targets: [
    { object: "tv_screen",   src: "/pages/ai-radio.html",      width: 1600, height: 900 },
    { object: "desk_tablet", src: "/pages/notes.html",         width: 768,  height: 1024 },
    { object: "east_wall",   src: "/pages/crm-kanban.html",    width: 1920, height: 1080 },
    { object: "curtain",     html: "<h1>Welcome</h1><p>...</p>" },
  ],
  fallbackMode: "placeholder",
});
```

That is the complete authoring API. **One module import, one array of targets.** The agent just needs to know mesh names (from `scene.traverse` / GLB node names / `object.name` in its own scene).

Reference impl we modeled on: `fimbox/html-in-canvas` on GitHub (PlayCanvas version). Three.js runtime lives at `/mnt/system/base/OpenVoiceUI/canvas-shared/html-surfaces.js`, synced into every tenant's `canvas-pages/_shared/`.

> **Load `threejs-canvas-integration` first** for the canvas page shell, import map, and CSP rules.

---

## Target spec

Each entry in `targets` is a single object:

| Field | Type | Purpose |
|---|---|---|
| `object` | `string` \| `THREE.Object3D` | Mesh name (walks `scene.traverse`) or direct mesh reference. Must be a `THREE.Mesh`. |
| `src` | `string` | URL of a canvas page to embed as an iframe. **Use this for most cases** — same-origin pages from `/pages/` work inside CSP. |
| `html` | `string` | Inline HTML string. Renders into a plain `<div>`. Good for small widgets. |
| `element` | `HTMLElement` | Use an existing DOM element you already built. |
| `width`, `height` | `number` | Source element size in pixels. Default 1024×1024. Pick aspect to match the mesh UV. |
| `materialSlot` | `string` | Which material map slot to drive (default `"map"`). Use `"emissiveMap"` for glowing screens that don't need scene lighting. |
| `refreshMs` | `number` | Iframe poll interval. Default 500. Set to `0` to disable (refresh only on interaction). |

Exactly one of `src`, `html`, `element` is required.

---

## Runtime handles

`mountHtmlSurfaces(...)` returns:

```javascript
surfaces.get("tv_screen")            // → surface handle for that name
surfaces.all()                       // → array of all surface handles
surfaces.mesh("tv_screen")           // → the THREE.Mesh for that surface
surfaces.refreshAll()                // → force re-upload of every surface
surfaces.dispose()                   // → remove listeners, free textures, remove DOM
surfaces.supported                   // → boolean: did the browser have texElementImage2D?
```

Per-surface handle:

```javascript
const tv = surfaces.get("tv_screen");
tv.navigate("/pages/other.html");    // swap the iframe src
tv.setHtml("<h1>New content</h1>");  // swap inline HTML (not for iframe mode)
tv.refresh();                        // force re-upload
tv.mesh                              // the THREE.Mesh
tv.sourceEl                          // the iframe/div being painted
tv.texture                           // the THREE.Texture (driving mesh.material.map)
```

---

## Full working example — GLB scene with named meshes

Agent loads a Meshy-generated living room and paints UIs on known surfaces:

```javascript
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { mountHtmlSurfaces } from "/pages/_shared/html-surfaces.js";

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, innerWidth/innerHeight, 0.1, 100);
camera.position.set(0, 1.7, 4);
scene.add(new THREE.AmbientLight(0xffffff, 0.6));
scene.add(new THREE.DirectionalLight(0xffffff, 0.9));

const gltf = await new GLTFLoader().loadAsync("/pages/living-room.glb");
scene.add(gltf.scene);

// Discover mesh names (first pass while building — remove once known)
gltf.scene.traverse(o => o.isMesh && console.log("mesh:", o.name));
// → mesh: tv_screen, mesh: coffee_table_tablet, mesh: wall_left, ...

const surfaces = mountHtmlSurfaces({
  scene, camera, renderer,
  targets: [
    { object: "tv_screen",           src: "/pages/ai-radio.html" },
    { object: "coffee_table_tablet", src: "/pages/inbox.html", width: 768, height: 1024 },
    { object: "wall_left",           src: "/pages/crm-kanban.html", width: 1600, height: 1000 },
  ],
  fallbackMode: "placeholder",
});

function animate() {
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
```

That's it. User can click buttons on the TV, type in the tablet, drag kanban cards on the wall.

---

## Browser support & fallback

| Capability | Behaviour |
|---|---|
| Chrome with `chrome://flags/#canvas-draw-element` **enabled** | Full live HTML + interaction. |
| Anything else (Safari, Firefox, Chrome with flag off) | Each target gets a `CanvasTexture` placeholder with instructions to enable the flag. Scene doesn't break. |

The module feature-detects at mount time — `surfaces.supported` tells you which branch fired. **Never ship a blank texture** — use `fallbackMode: "placeholder"` (default) unless you have a reason to hide the surface entirely (`"hidden"`).

---

## Rules that bite

1. **Mesh must exist and be a `THREE.Mesh`** — Groups/Object3Ds without geometry are skipped with a console warning. If your GLB has a parent Group named "tv_screen" but the actual mesh is a child, point at the child (`"tv_screen_glass"` or similar).
2. **Mesh UVs must span 0→1 over the screen area.** If UVs are tiled or clamped, the HTML will tile or clamp too. Re-UV-unwrap the screen face in Blender or use `PlaneGeometry` proxies for now.
3. **Iframes can't be observed from outside.** Inline HTML refreshes on `MutationObserver`; iframes poll every 500ms (configurable via `refreshMs`) plus refresh after every synthetic interaction.
4. **Canvas CSP** (`/pages/_shared/` is same-origin so this just works). External scripts still need allowlisting in `canvas.py`.
5. **Size in pixels** — percentages produce a 0×0 upload. Set `width`/`height` per target or accept the 1024 default.
6. **One mount per scene.** Calling `mountHtmlSurfaces` twice installs duplicate listeners. If you need to add surfaces later, call `surfaces.dispose()` and re-mount, or extend the module.

---

## When to skip this skill

- Target mesh is a particle/sprite or uses a custom shader that ignores `material.map` → write the low-level pattern yourself (see below).
- You need the HTML to render stereoscopically in VR → not supported in this module yet.
- You want the surface to be a **cube** or **sphere** with HTML wrapping → UV math gets weird; use multiple planar surfaces instead.

---

## Low-level reference (for building your own variant)

For cloth, skinned meshes, shader surfaces, or anything the declarative module doesn't cover, here's the raw mechanism:

1. `canvas.setAttribute("layoutsubtree", "true")` — lay out DOM descendants of the WebGL canvas.
2. Create source element as a **child of `renderer.domElement`**, size in px, `pointer-events: none`.
3. Create a `THREE.Texture`, set `image = { width, height }`, `needsUpdate = true`, then `renderer.initTexture(tex)` to materialize the GL handle.
4. Upload loop:
   ```javascript
   const glTex = renderer.properties.get(tex).__webglTexture;
   gl.bindTexture(gl.TEXTURE_2D, glTex);
   gl.texElementImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, sourceEl);
   ```
5. Heartbeat: `canvas.requestPaint()` + one-shot `"paint"` event listener — triggers the upload after the browser rasterizes.
6. Flip V: `texture.repeat.set(1, -1); texture.offset.set(0, 1);` — HTML paints top-down, three.js UVs go bottom-up.
7. Interaction:
   - Raycast mesh → `hit.uv`
   - `clientX = elRect.left + hit.uv.x * w; clientY = elRect.top + (1 - hit.uv.y) * h;`
   - Temporarily: `sourceEl.style.pointerEvents = "auto"; sourceEl.style.zIndex = "999999";`
   - `const target = document.elementFromPoint(clientX, clientY);`
   - `target.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, clientX, clientY, ... }))`
   - Restore `pointer-events: none`, `zIndex: ""`
   - `refresh()` so the DOM's reaction paints back onto the surface

Read `/mnt/system/base/OpenVoiceUI/canvas-shared/html-surfaces.js` end-to-end — the module is ~300 lines and every branch is commented.

The canonical cloth variant (with Ammo physics soft-body, text selection, range slider support, text input focus maintenance) is `fimbox/html-in-canvas` → `plugins/html-cloth.mjs` on GitHub. PlayCanvas code, but the technique is engine-agnostic.

---

## Testing checklist

1. Enable `chrome://flags/#canvas-draw-element` → Relaunch.
2. Load a canvas page with `mountHtmlSurfaces(...)`. Check console — no warnings about missing meshes.
3. Verify `surfaces.supported === true` in DevTools.
4. Texture appears on the first mesh within 2 frames. If blank: confirm `sourceEl` ended up as a child of `renderer.domElement`, width/height set in px, and `renderer.initTexture` was called (the module handles these automatically; manual users beware).
5. Hover → mesh should show hover cursor. Click a button on the 3D surface → it should fire in DOM. Type in an input → characters land.
6. Disable the flag → reload → placeholder texture explains the requirement.

---

## Module source of truth

- Master: `/mnt/system/base/OpenVoiceUI/canvas-shared/html-surfaces.js`
- Deploy: `bash scripts/jambot-deploy-canvas-shared.sh` (rsyncs into every tenant's `canvas-pages/_shared/`)
- Import URL inside a canvas page: `/pages/_shared/html-surfaces.js` (same-origin, within CSP)

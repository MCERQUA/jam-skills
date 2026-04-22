---
name: desktop-resolution-profile
description: "How webtop desktop resolution + ground-tag downscale + Chrome zoom affect MAI-UI-8B grounder accuracy and context. Read this before tuning viewer browser size, setting OVUI_GROUND_TAG_W/H env, or passing resolution_tag to /api/ui_ground. Trigger: 'resolution', 'downscale', 'ground tag', 'click accuracy', 'browser size', 'zoom', 'agent cant see', 'screenshot too small'."
---

# desktop-resolution-profile

**The counterintuitive thing:** higher desktop resolution ≠ better agent accuracy. It's a tradeoff between *context per screenshot* and *per-pixel precision at ground-space*.

## Two different "resolutions" to keep in your head

1. **Native X screen resolution** — what the webtop compositor (KWin) renders at. Controlled by Selkies: it **auto-matches the viewer's browser viewport**. You resize the browser window → X screen resizes. This is your *real estate*: bigger means more apps/panels fit without overlap.

2. **Ground-space tag (`tag_w × tag_h`)** — the dimensions the bridge downscales the screenshot to before sending to MAI-UI-8B. Currently defaults per-call via auto-detect; can override with `resolution_tag: "WxH"` in the `/api/ui_ground` request body. This is the *pixel budget the grounder thinks in*.

The grounder **always emits coords in `[0, 1000]` normalized space**, not in pixel space. The bridge rescales back to native pixels after receiving the response.

## Downscale tradeoff table

For a native desktop at `native_w × native_h`, downscaled to `tag_w × tag_h` (Lanczos):

| Downscale factor | Effect on grounder |
|---|---|
| ≤ 1.0× (upscale or equal) | No detail loss, every native pixel preserved. Usually wasteful — padding doesn't help |
| 1.0-1.25× | Minor softening, text still crisp. **Optimal zone.** |
| 1.25-1.5× | Small icons start blending with neighbors; text at 12px becomes ambiguous |
| 1.5-2.0× | Panel icons merge; dense toolbars become blurs |
| > 2.0× | Fine UI unreadable at ground-space. Grounder guesses or fails |

The auto-picker (`_auto_ground_tag` in the bridge) targets ≤ 1.5× by default, rounding to the nearest 256-multiple, capping at 1536×1152 (MAI-UI-8B was trained around 1024×768 — beyond 1.5× you burn inference tokens with negligible accuracy gain).

## Chrome zoom — similar principle

Browser zoom affects **DOM element render size**, which in turn affects their appearance in screenshots regardless of downscale:

| Zoom | Trade-off |
|---|---|
| 50% | See 2× more page per screenshot. Text + buttons become ~8-12 px in ground-space → grounder may miss them |
| 100% | Standard rendering. Buttons are ≥ 24 px native → readable through reasonable downscale |
| 125-150% | Bigger UI elements, easier grounder hits. Less context per shot |

**Rule of thumb:** zoom is a "context vs precision" knob for in-browser agent work, same shape as desktop resolution vs ground-tag.

## Viewer's browser window size matters (a lot)

Since Selkies matches X screen to viewer's browser viewport:

- **6 tiled 600×400 windows** (common monitor layout) → each agent gets a 600×400 desktop. KDE panels eat ~60 px of the 400 vertical = usable canvas ~340 px. Cramped.
- **Full-screen 1920×1080** → agent has real room. 2× downscale in ground-space (default) works because text is ≥ 20 px native.
- **4K maximized** → native 3840×2160 → auto-tag picks 1536×1152 = 2.5× downscale. Text that was 16 px native → ~6 px in ground-space. Legibility starts to break for dense UIs.

## Per-call override

Agents can override the auto-tag per-request based on what they're doing:

```bash
# Overview: find one element on a long page — higher res for more context
curl -X POST http://localhost:8090/api/ui_ground \
  -H "Authorization: Bearer $OVUI_BRIDGE_AUTH_TOKEN" \
  -d '{"intent":"locate the Save button anywhere on this form",
       "resolution_tag":"1536x1152"}'

# Precision: click a tiny X on a dialog — lower res for sharper per-pixel
curl -X POST http://localhost:8090/api/ui_ground \
  -H "Authorization: Bearer $OVUI_BRIDGE_AUTH_TOKEN" \
  -d '{"intent":"click the close X on this alert",
       "resolution_tag":"768x576"}'
```

Allowed range: `256 ≤ W,H ≤ 4096`. Values outside the range silently fall back to auto-detect.

## Screen introspection — ask first, act second

`GET /api/screen_info` returns the bridge's current view:

```json
{
  "ok": true,
  "native_w": 1280, "native_h": 720,
  "ground_tag_default": [1024, 768],
  "downscale_factor": 1.25,
  "ground_tag_env": [1024, 768],
  "detection_source": "xdpyinfo"
}
```

Use this at the start of a session to calibrate. If `native_w × native_h` came back as `1024 × 768` AND `detection_source` is `"env-fallback"`, the bridge couldn't detect the real native — log this, try to verify another way (`xrandr --current` from a terminal tool).

## Tuning playbook

- **User's browser window is tiny (< 800×600):** advise opening fullscreen for agent work OR expect reduced precision on small UI. Don't attempt fine-grained targeting; prefer broad region crops.
- **User's browser window is 1024×768 to 1600×1200:** optimal. `ground_tag_default` ≈ native, minimal downscale. Default auto-tag wins.
- **User's browser window is big (> 2000×1200):** use smaller `resolution_tag` for precision clicks (640×480 or 768×576), larger `resolution_tag` for "find element on this crowded screen" queries (1536×1152).
- **On a 4K TV or very-high-DPI display:** default auto-tag is 1536×1152. Fine for overview. For element-level clicks, drop to 1024×768.

## Region crop — the other accuracy lever

Parallel to resolution_tag: the `region: [x, y, w, h]` parameter crops the screenshot BEFORE downscale. So a 2560×1440 native desktop with `region: [800, 400, 600, 300]` gets downscaled from a 600×300 crop (not the full 2560×1440). Much higher effective pixel density in ground-space.

Combine them:
```bash
# "Click something specific inside a known region" — highest accuracy
{"intent":"click the OK button in the dialog",
 "region":[800,400,400,300],
 "resolution_tag":"400x300"}
```

Bridge receives `region` coords in full-screen pixels, downscales to tag, grounder returns [0,1000], bridge rescales + adds region offset → final coords are full-screen pixels.

## Debugging mismatched clicks

If `ovui_find_and_click` reports `clicked: true` but nothing happened:

1. Check `ground_w/ground_h` in the response — was downscale aggressive (>1.5×)? If so, try a lower `resolution_tag`.
2. Check `ground_raw` (normalized [0, 1000]) and the mapping to pixel space. Wildly off coordinates usually mean the grounder picked wrong element due to downscale ambiguity.
3. Check `ground_tag_source`:
   - `"explicit"` — caller set resolution_tag; if results are poor, the tag is probably wrong for this scene
   - `"auto"` — bridge detected native + picked, usually right
   - `"env-fallback"` — bridge couldn't detect, using env vars. Fix the env or fix xdpyinfo access in the container
4. For panel/taskbar clicks that report `clicked:true` but don't trigger: not a resolution issue. See `todo_xdotool_kwin_wayland_panel` + selkies-ws injection path.

## Cross-refs

- `OVUI_GROUND_TAG_W` / `OVUI_GROUND_TAG_H` env vars (fallback)
- Bridge handler: `/opt/ovui/ovui_bridge.py::handle_ui_ground` + `::handle_screen_info`
- Selkies WS input-injection — `ydotool_and_selkies_ws_input_paths` memory
- Phase 5.5 grounder architecture — memory references

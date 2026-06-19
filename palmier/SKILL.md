# Palmier Pro — Claude Code Skill

Palmier Pro is a Swift-native video editor for macOS built for AI-first workflows. YC S24. Open-source (GPLv3). When the app is open it exposes a local MCP server — agents can generate media, edit the timeline, and export, all without leaving the project.

## When to use

- User wants to create or edit a video on the Mac using AI generation (Kling, Seedance, Veo, Grok)
- Automating video production: generate clips, arrange on timeline, export
- Agent needs to programmatically place, trim, reorder, or inspect clips in a running project
- Building video pipelines where Claude drives the timeline directly

## Requirements

- macOS 26 (Tahoe) on Apple Silicon (M-series) only
- App must be open for MCP to work — no headless mode
- Editor and MCP are free; AI generation (generate_video, generate_image, generate_audio) requires a paid account with credits

## Installation

```bash
# Download DMG (v0.3.3 as of 2026-06-18, check GitHub for latest)
curl -L -o /tmp/PalmierPro.dmg \
  https://github.com/palmier-io/palmier-pro/releases/latest/download/PalmierPro.dmg

# Mount and install
hdiutil attach /tmp/PalmierPro.dmg -nobrowse
cp -R /Volumes/PalmierPro/PalmierPro.app /Applications/
hdiutil detach /Volumes/PalmierPro

# Launch
open /Applications/PalmierPro.app
```

On macmini-office@mesh, Palmier Pro is already installed at `/Applications/PalmierPro.app`.

## MCP Connection

Palmier exposes an HTTP MCP server at `http://127.0.0.1:19789/mcp` while the app is running.

**Connect Claude Code:**
```bash
claude mcp add --transport http palmier-pro http://127.0.0.1:19789/mcp
```

**Verify it's running:**
```bash
curl -s --max-time 3 http://127.0.0.1:19789/mcp
# Returns ": connected" if up
```

**In `~/.claude.json` or project MCP config:**
```json
{
  "mcpServers": {
    "palmier-pro": {
      "type": "http",
      "url": "http://127.0.0.1:19789/mcp"
    }
  }
}
```

## MCP Tool Reference

### Session start — always call first
| Tool | Description |
|------|-------------|
| `get_timeline` | Returns project settings (fps, resolution, totalFrames), all tracks + clips with IDs. **Always call at start of session** — clipId/trackId from here are what every other tool accepts. Also returns `canGenerate` (false = user not signed in/subscribed). |
| `get_media` | Returns all media assets in the library with their IDs (mediaRef). Call before referencing any asset. |
| `list_models` | Lists available AI models for generation. |

### Inspect
| Tool | Description |
|------|-------------|
| `inspect_media` | View a media asset: images (with EXIF), video (sample frames + transcript), audio (transcript). Supports windowed inspection with `startSeconds`/`endSeconds`. Pass `overview=true` for a storyboard grid. |
| `inspect_timeline` | See the composited output at a given frame — all tracks blended with transforms applied. Use to verify edits. |
| `search_media` | Semantic search by visual content or spoken words. Returns source-second ranges. |

### Timeline editing
| Tool | Description |
|------|-------------|
| `add_clips` | Place one or more media assets on the timeline. Can auto-create tracks (omit `trackIndex`) or target existing ones. Overlap on a track overwrites existing clips. |
| `remove_clips` | Remove clips by ID. Removes linked audio/video partners together. |
| `remove_tracks` | Remove whole tracks and all clips on them. |
| `move_clips` | Move clips to a new track and/or frame position. Linked partners follow. |
| `set_clip_properties` | Set duration, trim, speed, volume, opacity, transform, or text content/style. Timing changes propagate to linked audio/video. |
| `set_keyframes` | Animate properties over time (use instead of `set_clip_properties` for volume/opacity to avoid clearing keyframe tracks). |
| `split_clip` | Split a clip at a frame boundary. |

### Text & captions
| Tool | Description |
|------|-------------|
| `add_texts` | Add text overlays to the timeline. |
| `add_captions` | Add caption groups (auto-fit bounding boxes). |

### AI generation (requires paid account + credits)
| Tool | Description |
|------|-------------|
| `generate_video` | Generate video with Kling V3, Seedance 2.0, Veo 3.1, or other models. Supports first/last frame control and reference images. Async — check `get_media` for `generationStatus`. |
| `generate_image` | Generate images. Placed in the media library. |
| `generate_audio` | Generate audio/music. |
| `upscale_media` | Upscale an existing clip or image. |
| `import_media` | Import media from a URL or local path into the project library. |

### Library management
| Tool | Description |
|------|-------------|
| `list_folders` / `create_folder` | Organize the media library into folders. |
| `move_to_folder` / `rename_media` / `rename_folder` | Reorganize assets. |
| `delete_media` / `delete_folder` | Remove assets from the library. |

## Core Agent Workflow

```
1. get_timeline          → get project state, track/clip IDs, fps, canGenerate
2. get_media             → get mediaRef IDs for all library assets
3. import_media / generate_* → add new assets to the library (async for generation)
4. add_clips             → place assets on timeline by frame
5. set_clip_properties   → trim, speed, volume, transform adjustments
6. inspect_timeline      → verify the composition looks right
7. (export via app UI or trigger export from agent chat)
```

**Async generation pattern:**
```
generate_video(...)     → returns immediately, status = "generating"
poll get_media()        → wait for generationStatus != "generating"/"downloading"
add_clips(mediaRef)     → place on timeline once ready
```

## Export formats

- MP4: H.264, H.265, ProRes
- NLE XML: Premiere Pro and DaVinci Resolve compatible

Export is triggered from the app UI or via the in-app agent chat. No direct MCP export tool currently.

## Pricing

| Tier | Price | Credits |
|------|-------|---------|
| Free | $0 | Editor + MCP, no generation |
| Pro | $29/mo (was $49) | 5,000 credits/mo |
| Max | $69/mo (was $99) | 12,000 credits/mo |

~5,000 credits ≈ 333 images or 3–7 min of video (varies by model/resolution). Editing is always free.

## Gotchas & Limitations

- **App must be running** — MCP server only lives while PalmierPro.app is open. If the socket returns nothing, check if the app crashed or was quit.
- **macOS 26 + Apple Silicon only** — no Intel Mac, no Linux, no Windows.
- **canGenerate check** — call `get_timeline` first; if `canGenerate` is false, generation tools will fail. User needs to sign in and subscribe.
- **Async generation** — `generate_video` / `generate_image` / `generate_audio` return immediately. Poll `get_media` for status: `generating → downloading → none` (none = ready). Don't call `add_clips` until status is `none`.
- **Track overlap overwrites** — placing a clip on an existing track that overlaps another clip trims/splits the existing clip. Use separate tracks to avoid overwrites.
- **No headless export** — export must be triggered from the UI. Agent can set up the timeline but can't fully automate the final export step.
- **Text clip trims** — text clips have no source media so trimStartFrame/trimEndFrame don't apply.
- **Caption groups** — clips sharing a `captionGroupId` come back as `captionGroups` in `get_timeline`, not in `clips`. Rows capped at 200 per group — use `startFrame`/`endFrame` pagination.

## GitHub

- Repo: https://github.com/palmier-io/palmier-pro
- Open source (GPLv3): editor, MCP server, agent chat are open; AI processing is closed
- Issues / support: founders@palmier.io or Discord: https://discord.com/invite/SMVW6pKYmg

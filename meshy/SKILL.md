---
name: meshy
description: SUPERSEDED — all 3D tasks (find, generate, rig, animate, retexture, remesh) are now unified in the `3d-models` skill. This stub redirects. Read `skills/3d-models/SKILL.md` instead.
metadata: {"openclaw": {"requires": {"env": ["MESHY_API_KEY"], "anyBins": ["curl", "python3"]}}}
---

# Meshy — superseded by the unified `3d-models` skill

All Meshy API coverage (text-to-3d, image-to-3d, multi-image, rigging, 587-action animation library, retexture, remesh, platform webhook auto-save) now lives in **`skills/3d-models/SKILL.md`** alongside Tripo3D fallback and Objaverse (free 800K-model FIND path).

**Read this instead:** `/home/node/.openclaw/skills/3d-models/SKILL.md`

The platform wiring (`/api/meshy/track`, webhook receiver at `api-social.jam-bot.com/webhooks/meshy`, auto-download to tenant `canvas-pages/`) is unchanged — `3d-models` documents the same endpoints.

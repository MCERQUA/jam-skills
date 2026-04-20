---
name: tripo-3d
description: SUPERSEDED — Tripo3D is now the fallback provider documented inside the unified `3d-models` skill. Read `skills/3d-models/SKILL.md` instead.
metadata: {"openclaw": {"requires": {"env": ["TRIPO_API_KEY"], "anyBins": ["curl", "python3"]}}}
---

# Tripo3D — superseded by the unified `3d-models` skill

Tripo3D is kept as a fallback provider when Meshy fails, rate-limits, or runs out of credits. Full Tripo API coverage (text-to-3d, image-to-3d, multi-view, rigging, animate_retarget, texture/stylize, mesh ops, format conversion) now lives under the "fallback" subsections of **`skills/3d-models/SKILL.md`**.

**Read this instead:** `/home/node/.openclaw/skills/3d-models/SKILL.md`

Base URL unchanged: `https://api.tripo3d.ai/v2/openapi` · Auth: `Authorization: Bearer $TRIPO_API_KEY`.

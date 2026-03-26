---
name: icon-generation
description: "Generate custom icons for canvas pages, tools, and categories. Use when the user needs icons, favicons, or visual assets. Has 1700+ pre-built Lucide icons and AI generation via Gemini."
---

# Icon Generation Skill

Generate custom icons for canvas pages, tools, categories, and anything the user needs. You have access to 1,700+ pre-built icons AND AI-powered custom icon generation via Gemini.

## CRITICAL: Base URL

**ALL API calls MUST use `http://openvoiceui:5001` as the base URL.**

```
# CORRECT:
curl -s http://openvoiceui:5001/api/icons/library/search?q=heart

# WRONG (will fail — openvoiceui is NOT on localhost inside openclaw):
curl -s http://localhost:5001/api/icons/library/search?q=heart
```

## When to Use

- **Creating a new canvas page** → ALWAYS generate a custom icon for it
- **User asks for an icon** → generate or find one
- **Building a tool/dashboard** → create icons for each section
- **Customizing the desktop** → generate themed icons

## CRITICAL: Be Creative with Icons

**DO NOT** make generic document/folder icons. Every icon should be UNIQUE and SPECIFIC to what it represents.

**Think about:**
- What does this page/tool actually DO? (not just "it's a document")
- What would a user RECOGNIZE at 48px? (distinctive shape, color, metaphor)
- What EMOTION or CATEGORY does it belong to? (playful, professional, technical, creative)

**Examples of GOOD icon prompts:**
- "A golden trophy with sparkles for a leaderboard page"
- "A magnifying glass over a bar chart for an analytics dashboard"
- "A paintbrush crossing a camera for a creative media tool"
- "A wrench inside a gear for a settings/configuration panel"
- "A rocket launching from a laptop for a deployment tool"
- "A shield with a checkmark for a security audit page"
- "A calendar with a clock overlay for a scheduling tool"

**Examples of BAD icon prompts (TOO GENERIC):**
- "A document icon" ← boring, tells user nothing
- "A page icon" ← useless
- "A blue square" ← zero information

## API Reference

### 1. Search Pre-Built Icons (Lucide Library — 1,700+ icons)

```bash
curl -s "http://openvoiceui:5001/api/icons/library/search?q=folder&limit=10"
```

Response:
```json
{"query": "folder", "count": 8, "icons": ["folder", "folder-check", "folder-open", ...]}
```

Use the icon URL: `/api/icons/library/folder.svg`

### 2. Generate Custom Icon (Gemini AI)

```bash
curl -s -X POST http://openvoiceui:5001/api/icons/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A golden trophy with sparkles for a leaderboard", "name": "leaderboard-trophy"}'
```

Response:
```json
{
  "url": "/api/icons/generated/leaderboard-trophy.png",
  "name": "leaderboard-trophy",
  "filename": "leaderboard-trophy.png",
  "prompt": "A golden trophy with sparkles for a leaderboard",
  "size": 45231
}
```

**Optional fields:**
- `name` — filename slug (auto-derived from prompt if omitted)
- `style` — override default style (default: "Windows XP style icon, clean vector art, vibrant colors, slight 3D shading")

### 3. List Generated Icons

```bash
curl -s http://openvoiceui:5001/api/icons/generated
```

Returns all previously generated icons with metadata.

### 4. Browse Full Icon Library

```bash
curl -s http://openvoiceui:5001/api/icons/library
```

Returns all 1,700+ icon names.

## Auto-Icon on Page Creation

When creating a new canvas page, ALWAYS:

1. **Think** about what makes this page unique — its purpose, its content, its vibe
2. **Generate** a custom icon that captures that uniqueness:
   ```bash
   curl -s -X POST http://openvoiceui:5001/api/icons/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "<descriptive, visual prompt>", "name": "<page-slug>-icon"}'
   ```
3. **Attach** the icon to the page using PATCH:
   ```bash
   curl -s -X PATCH http://openvoiceui:5001/api/canvas/manifest/page/<page-id> \
     -H "Content-Type: application/json" \
     -d '{"icon": "<url from step 2>"}'
   ```
   Example:
   ```bash
   curl -s -X PATCH http://openvoiceui:5001/api/canvas/manifest/page/insurance-forms-interactive \
     -H "Content-Type: application/json" \
     -d '{"icon": "/api/icons/generated/insurance-forms-icon.png"}'
   ```
   The field is `"icon"` — NOT `"iconUrl"`, NOT `"icon_url"`. The URL must be the exact value from the generate response.

4. The desktop will display the icon automatically on next refresh (within 30 seconds).

**NEVER** copy the icon file manually. **NEVER** guess field names. Use the PATCH call above exactly.

## Style Guidelines

The default style produces Windows XP-era icons — vibrant, slightly 3D, recognizable at small sizes. You can override with:

- `"style": "flat minimalist, single color, modern"` — for clean/modern UIs
- `"style": "pixel art, 16-bit retro game style"` — for game-related pages
- `"style": "professional corporate, muted colors, clean lines"` — for business tools
- `"style": "playful cartoon, bright colors, rounded shapes"` — for fun/entertainment

## User's Generated Icons

Users can find all their generated icons in **File Explorer → Icons → generated/**. Each icon has a `.meta.json` sidecar with the original prompt, so they can regenerate or iterate.

---
name: stitch
description: "Google Stitch AI-powered UI design generation. Use when the user mentions stitch, UI design generation, design-to-code, screen generation, or wants to create/edit UI mockups programmatically."
metadata:
  version: 1.1.0
---

# Google Stitch — AI UI Design Generation

Generate production-ready UI designs from text prompts. Outputs HTML with Tailwind CSS.

## ⚠️ CRITICAL RULES — READ FIRST

1. **Call stitch-mcp.sh DIRECTLY via `exec`.** NEVER spawn a z-code/maxcode sub-agent to use Stitch. The API calls are simple HTTP requests — a sub-agent adds unnecessary polling layers and will hit the 300s timeout. Just `exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh ...")`.

2. **Use DESKTOP for website mockups.** Set `"deviceType": "DESKTOP"` when creating projects for website designs. MOBILE is for app mockups only.

3. **Generation is ASYNC — verify before claiming success.** After `generate_screen_from_text`, the response may say "success" before the screen is fully ready. You MUST verify with `list_screens` — if the list is empty, wait 30 seconds and check again (up to 3 retries). NEVER tell the user "generated successfully" until `list_screens` returns actual screen data.

4. **One screen at a time.** Generate one screen, verify it exists, THEN generate the next. Don't batch.

## How To Use

Run the helper script with `exec` (ALWAYS exec, never sub-agents):

```bash
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh <tool_name> '<json_arguments>'")
```

### Quick Start — Website Mockup

Follow this exact sequence for website design mockups:

```bash
# Step 1: Create project (DESKTOP for websites)
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh create_project '{\"title\": \"My Website\", \"deviceType\": \"DESKTOP\"}'")
# → Save the project ID from the response

# Step 2: (Optional) Create design system for consistency
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh create_design_system '{\"projectId\": \"PID\", \"colorMode\": \"DARK\", \"font\": \"INTER\", \"roundness\": \"ROUND_EIGHT\", \"customColor\": \"#3b82f6\"}'")

# Step 3: Generate a screen with a DETAILED prompt
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh generate_screen_from_text '{\"projectId\": \"PID\", \"prompt\": \"Homepage for a tech e-commerce store. Full-width hero with gradient background and bold headline. Navigation bar with logo left, links center, cart icon right. Featured products grid below hero with 4 cards showing product image, name, price, and Add to Cart button. Dark theme, modern typography.\", \"modelId\": \"GEMINI_3_PRO\"}'")

# Step 4: WAIT then verify — generation takes 1-3 minutes
# Wait 60 seconds, then check:
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh list_screens '{\"projectId\": \"PID\"}'")
# If empty, wait 30s more and retry (up to 3 times)

# Step 5: Get screen HTML + screenshot
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh get_screen '{\"name\": \"projects/PID/screens/SID\", \"projectId\": \"PID\", \"screenId\": \"SID\"}'")

# Step 6: Download the HTML and save as canvas page
exec("curl -L 'DOWNLOAD_URL' -o /app/runtime/canvas-pages/mockup-homepage.html")
```

### More Examples

```bash
# List all projects
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh list_projects '{}'")

# Edit an existing screen
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh edit_screens '{\"projectId\": \"PID\", \"selectedScreenIds\": [\"SID\"], \"prompt\": \"Change the button color to blue\"}'")

# Generate design variants
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh generate_variants '{\"projectId\": \"PID\", \"selectedScreenIds\": [\"SID\"], \"prompt\": \"Explore different layouts\", \"variantOptions\": {\"variantCount\": 3, \"creativeRange\": \"EXPLORE\"}}'")
```

## Available Tools (verified against live API)

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects. Optional: `{"filter": "view=owned"}` or `"view=shared"` |
| `get_project` | Get project details. `{"name": "projects/{id}"}` |
| `create_project` | Create project. `{"title": "Name"}` |
| `list_screens` | List screens. `{"projectId": "ID"}` |
| `get_screen` | Get screen HTML/image. `{"name": "projects/P/screens/S", "projectId": "P", "screenId": "S"}` |
| `generate_screen_from_text` | Generate from prompt. `{"projectId": "ID", "prompt": "...", "modelId": "GEMINI_3_PRO", "deviceType": "DESKTOP"}` |
| `edit_screens` | Edit screens with prompt. `{"projectId": "ID", "selectedScreenIds": ["SID"], "prompt": "..."}` |
| `generate_variants` | Create variants. `{"projectId": "ID", "selectedScreenIds": ["SID"], "prompt": "...", "variantOptions": {...}}` |

**⚠️ These tools do NOT exist in the API (removed):** `delete_project`, `upload_screens_from_images`, `create_design_system`, `update_design_system`, `list_design_systems`, `apply_design_system`. The design system is created automatically when generating screens — pass brand colors/style info in the prompt instead.

**⚠️ `deviceType` goes on `generate_screen_from_text`**, NOT on `create_project`. Use `"DESKTOP"` for website mockups, `"MOBILE"` for app mockups.

## Writing Effective Prompts

### Prompt Structure (in order)
1. **Screen purpose** — dashboard, login, landing page, settings, profile
2. **Core UI components** — buttons, cards, charts, nav bars, forms, lists
3. **Layout** — grid, stacked, scrollable, centered, sidebar+content, 2-column
4. **Style & theme** — dark/light, colors, rounded corners, typography
5. **Data content** — placeholder data, prices, status labels, sample text
6. **Branding** — app name, logo placement, accent colors

### Good Prompts
- "Design a login page with email and password fields, a 'Remember Me' checkbox, a 'Forgot Password' link, and a gradient purple-to-blue background"
- "Dashboard with sidebar nav on left, main content area showing 4 KPI cards at top, line chart below, and recent activity table at bottom. Dark theme, Inter font, rounded-8 corners"
- "Product detail page for a Japandi-styled tea store. Hero image top, product info below. Neutral minimal colors, black buttons, soft elegant serif font"

### Bad Prompts (avoid these)
- "Create a login page" (too vague)
- "Make it better" (not specific)
- "Add more details" (no direction)

### Iteration Rules
1. **One change at a time** — never combine layout changes with component additions
2. **Be surgical** — "Change the hero section background to gradient" not "update the page styling"
3. **Reference precisely** — "primary button on sign-up form" not "the button"
4. **Use directional language** — "left/middle/right", "above/below"
5. **Keep prompts under 5000 characters** — longer prompts drop components

### Design Token Seeding
For consistency: "8-pt grid, border-radius 12, font Inter, sizes sm/md/lg, primary #3b82f6, surface #1e1e2e"

## Generation Notes
- **GEMINI_3_PRO** = higher quality, **GEMINI_3_FLASH** = faster
- Generation takes 1-3 minutes — do NOT retry on connection errors
- If you get a timeout, wait and check with `list_screens` then `get_screen`
- If response has `output_components` with suggestions, present them to the user
- Create a design system FIRST for consistent multi-screen projects
- **After calling `generate_screen_from_text`:** Wait 60 seconds, then call `list_screens`. If empty, wait 30s and retry up to 3 times. The API may return before the screen is indexed.
- **NEVER say "generated successfully" until you have confirmed the screen exists in `list_screens`**
- If after 3 retries the screen list is still empty, tell the user the generation may have failed and offer to retry with a different prompt

## Device Types & Variant Options
- **deviceType** (on `generate_screen_from_text`)**: MOBILE, DESKTOP, TABLET, AGNOSTIC
- **modelId:** GEMINI_3_PRO (quality) or GEMINI_3_FLASH (speed)
- **creativeRange (variants):** REFINE (subtle), EXPLORE (balanced), REIMAGINE (radical)
- **aspects (variants):** LAYOUT, COLOR_SCHEME, IMAGES, TEXT_FONT, TEXT_CONTENT

### Design System via Prompts
There is no `create_design_system` API tool. Instead, specify design tokens directly in your generation prompts:
- Colors: "primary green #22c55e, secondary amber #f59e0b, background #0a0a0a"
- Typography: "Use Space Grotesk for headlines, Inter for body"
- Corners: "border-radius 8px rounded corners"
- Spacing: "8-pt grid spacing system"

## Downloading Screen Assets
The `get_screen` response includes download URLs:
- `htmlCode.downloadUrl` — full HTML with Tailwind CSS
- `screenshot.downloadUrl` — PNG screenshot
- `figmaExport.downloadUrl` — Figma export
Use `curl -L <url>` to download.

## Canvas Page Integration
To use Stitch HTML as a canvas page:
1. Download HTML via `get_screen` → `htmlCode.downloadUrl`
2. Strip any `<script src="cdn.tailwindcss.com">` tags
3. Inline the CSS styles
4. Add the postMessage bridge for interactive elements
5. Save as a canvas page

---
name: stitch
description: "Google Stitch AI-powered UI design generation. Use when the user mentions stitch, UI design generation, design-to-code, screen generation, or wants to create/edit UI mockups programmatically."
metadata:
  version: 1.0.0
---

# Google Stitch — AI UI Design Generation

Generate production-ready UI designs from text prompts. Outputs HTML with Tailwind CSS.

## How To Use

Run the helper script with `exec`:

```bash
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh <tool_name> '<json_arguments>'
```

### Quick Examples

```bash
# List all projects
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh list_projects '{}'

# Create a new project
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh create_project '{"title": "My App"}'

# List screens in a project
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh list_screens '{"projectId": "PROJECT_ID"}'

# Generate a screen from a text prompt
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh generate_screen_from_text '{"projectId": "PROJECT_ID", "prompt": "A modern login page with dark theme and gradient background", "modelId": "GEMINI_3_PRO"}'

# Get screen details (HTML + screenshot URLs)
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh get_screen '{"name": "projects/PID/screens/SID", "projectId": "PID", "screenId": "SID"}'

# Edit an existing screen
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh edit_screens '{"projectId": "PID", "selectedScreenIds": ["SID"], "prompt": "Change the button color to blue"}'

# Generate design variants
bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh generate_variants '{"projectId": "PID", "selectedScreenIds": ["SID"], "prompt": "Explore different layouts", "variantOptions": {"variantCount": 3, "creativeRange": "EXPLORE"}}'
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects. Optional: `{"filter": "view=owned"}` or `"view=shared"` |
| `get_project` | Get project details. `{"name": "projects/{id}"}` |
| `create_project` | Create project. `{"title": "Name"}` |
| `delete_project` | Delete project (PERMANENT — confirm with user first). `{"name": "projects/{id}"}` |
| `list_screens` | List screens. `{"projectId": "ID"}` |
| `get_screen` | Get screen HTML/image. `{"name": "projects/P/screens/S", "projectId": "P", "screenId": "S"}` |
| `generate_screen_from_text` | Generate from prompt. `{"projectId": "ID", "prompt": "...", "modelId": "GEMINI_3_PRO"}` |
| `upload_screens_from_images` | Upload images as screens. `{"projectId": "ID", "images": [{"fileContentBase64": "...", "mimeType": "image/png"}]}` |
| `edit_screens` | Edit screens with prompt. `{"projectId": "ID", "selectedScreenIds": ["SID"], "prompt": "..."}` |
| `generate_variants` | Create variants. `{"projectId": "ID", "selectedScreenIds": ["SID"], "prompt": "...", "variantOptions": {...}}` |
| `create_design_system` | Create design system. See theme options below |
| `update_design_system` | Update design system by name |
| `list_design_systems` | List design systems. Optional `{"projectId": "ID"}` |
| `apply_design_system` | Apply to screens. `{"projectId": "ID", "selectedScreenIds": ["SID"], "assetId": "AID"}` |

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
- If you get a timeout, wait and check with `get_screen`
- If response has `output_components` with suggestions, present them to the user
- Create a design system FIRST for consistent multi-screen projects

## Design System Theme Options
- **colorMode:** LIGHT, DARK
- **font:** INTER, ROBOTO, DM_SANS, GEIST, SORA, MANROPE, SPACE_GROTESK, MONTSERRAT, and 21 more
- **roundness:** ROUND_FOUR, ROUND_EIGHT, ROUND_TWELVE, ROUND_FULL
- **creativeRange (variants):** REFINE (subtle), EXPLORE (balanced), REIMAGINE (radical)
- **aspects (variants):** LAYOUT, COLOR_SCHEME, IMAGES, TEXT_FONT, TEXT_CONTENT
- **deviceType:** MOBILE, DESKTOP, TABLET, AGNOSTIC

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

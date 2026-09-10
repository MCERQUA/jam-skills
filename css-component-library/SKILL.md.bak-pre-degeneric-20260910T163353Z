---
name: css-component-library
description: "Build-from menu of 119 curated copy-paste CSS components (buttons, cards, loaders, text effects, backgrounds, hover, borders, forms) — each with HTML+CSS, primary selector, usage note. TRIGGER when building or styling a website/page and you want ready-made on-brand effects instead of hand-writing animations. Composes with premium-web-design."
---

# CSS Component Library — Social Jam Build Menu

**Use this skill whenever you are building or styling a website/page** and want ready-made,
on-brand CSS effects instead of hand-writing animations from scratch. 119 curated components
(buttons, cards, loaders, text effects, backgrounds, hover, borders, forms, misc) — each with
copy-paste HTML+CSS, a primary selector, and a usage note. Built by Danielle's agent; this is
the agent-facing layer that turns it into a build-from menu.

## Files
- `COMPONENT-MENU.md` — the human/agent **recipe menu**: read this to pick components by section.
  Has the agent protocol, section→component composition recipes, and every component (code + usage).
- `component-catalog.json` — machine-readable index `[{name,category,selector,usage,html,css}]` ×119.
  Use for programmatic selection (filter by category, grab `css`+`html`, apply `selector`).
- Visual gallery (browse with live previews): Danielle's canvas page `css-effects-library.html`.

## How to use (build-from-menu protocol)
1. **Map page section → category:**
   hero → `text` + `backgrounds` + `buttons` · feature grid → `cards` + `hover` ·
   pricing → `cards` + `borders`(featured tier only) + `buttons` · contact/quote → `forms` + `buttons` ·
   any async → `loaders`.
2. Open `COMPONENT-MENU.md`, find the category, pick a component, **copy its CSS into a `<style>`
   block + its HTML into the markup**, apply the listed selector.
3. **Honor the usage note** — most say "one per viewport" / "verify 4.5:1 contrast" / "labelled input".
   One primary CTA treatment per page; don't mix three glow buttons.
4. For programmatic builds, read `component-catalog.json` and select by `category`/`name`.

## Quick category reference
| Category | Count | For |
|---|---|---|
| buttons | 18 | CTAs, submits |
| cards | 12 | feature/pricing/testimonial tiles |
| forms | 8 | inputs, focus states (label + focus ring required) |
| loaders | 18 | async feedback |
| text | 20 | animated headlines (1/viewport) |
| backgrounds | 10 | section ambiance (contrast-check) |
| hover | 13 | desktop micro-interactions |
| borders | 11 | draw the eye to a featured element |
| misc | 9 | badges, tooltips, accents (sparingly) |

## Maintaining
The catalog is GENERATED from the `effects` array in Danielle's `css-effects-library.html`
(the source of truth). To regenerate after she adds components: re-run the extractor
(`/tmp/csslib/gen-menu.py` pattern — parse the array → emit MENU.md + catalog.json).

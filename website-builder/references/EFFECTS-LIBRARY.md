# Effects Library — liftable, commented design references

Self-contained HTML references the builder can **study and lift from** when a brief calls
for premium/modern visual polish (dark "AI-product" aesthetics, glassmorphism, glow). Open
the file in a browser to see each effect live; every technique is commented inline. Lift the
specific block you need — don't paste a whole kit into a client site.

> When to reach for these: a brief asks for a sleek/modern/premium/"SaaS" or AI-tool feel,
> dark UI, glass panels, or tasteful glow. **Do NOT** use on home-service conversion sites
> where speed + clarity win (see [CONVERSION-RULES.md](../CONVERSION-RULES.md)) — heavy
> blur/glow hurts mobile PageSpeed and buries the phone CTA. Match the tool to the brief.

> ## 📥 INTAKE — this is a GROWING collection (Mike is gathering more Fable examples)
> **Status (2026-06-11):** 2 Fable reference files saved (`glow-glass-kit.html`,
> `off-catalog-components.html`). More incoming — Mike is collecting examples to review the
> full set in one pass before the component break-out runs. **Batch extraction is DEFERRED
> until then** (tracked in the void: `ovh-fable-components`).
>
> **To add a new example later:** (1) save the raw HTML verbatim as `references/<kebab-name>.html`
> — it is a PRESERVED ORIGINAL, never edited/deleted; (2) append each of its components to
> `components/_manifest.json` (slug, name, source, category, `conversion_safe`, `vars`,
> `status:"pending"`, + `conversion_note` if it maps to a CONVERSION-RULE); (3) add a one-row
> summary to the catalog below. When the collection is complete, run the break-out per
> `components/README.md` (delegate to a cheaper LLM; `components/magnetic-cta.html` is the
> worked exemplar of the generic + `{{vars}}` + RGB-triplet-accent pattern).

---

## glow-glass-kit.html — gradient borders · cursor spotlight · colored glass · ambient bloom

Six techniques, each driven by **one accent custom property** (raw RGB triplet, e.g.
`--violet: 168 85 247`) so any block re-themes to a brand color in one line via
`rgb(var(--a) / <alpha>)`.

| # | Technique | What it is | Lift when |
|---|-----------|-----------|-----------|
| 1 | **Gradient glow border** (`.glow-border`) | A `::before` with `padding:1px` painted with a gradient, then `mask-composite: exclude` keeps only the 1px ring; a blurred `::after` clone is the glow. No real border, no extra markup. Theme per-instance with `--edge`. | Feature cards, pricing tiles, hero panels that need a lit edge. |
| 2 | **Cursor-spotlight border** (`.spotlight`) | Same mask trick, but a `radial-gradient` centered on `--mx/--my` updated by ~6 lines of JS on `mousemove`; a faint white ring keeps the edge visible at rest. | Interactive card grids, "pick a plan/tool" selectors. |
| 3 | **Colored glass pills** (`.pill`, `--a` accent) | Translucent base + `backdrop-filter: blur+saturate`, 1px white edge, inset top highlight, hover→colored tint + bloom shadow. `.is-active` = persistent selected state. | Toolbars, filter/segment controls, tag chips. |
| 4 | **Glass tooltip** (`.tooltip`, pure CSS) | Hover/`focus-within` reveal, glass surface + gradient edge, sprung scale-in. Accessible (works on focus). | Inline help, control labels. |
| 5 | **Ambient bloom** (`.bloom`) | A blurred radial blob behind content for cheap depth. | Section/hero backgrounds. |
| 6 | **Solid colored-glass button** (`.btn-solid`) | Always-lit gradient fill + inset highlight + outer glow. | Primary CTA on dark surfaces. |

**Conventions to copy:**
- Define accents as **space-separated RGB triplets** (`--violet: 168 85 247`), not hex — lets you build `rgb(var(--violet) / .3)` tints at any opacity from one value.
- The `mask-composite` ring trick (blocks 1, 2, 4) is the reusable primitive — learn it once, reuse everywhere a gradient/animated border is wanted.
- Always ship the `@media (prefers-reduced-motion: reduce)` guard (already in the kit) — required for accessibility.
- All effects are GPU-cheap **except** stacked `backdrop-filter` blurs; use sparingly on mobile and never on a conversion-critical hero.

---

## off-catalog-components.html — 20 original interaction specimens

A larger foundry of from-scratch interactions across **type · reveal · action · input · nav ·
surface · glass**, each with a live telemetry readout. Highlights:
- **Conversion "Workhorses"** (safe on home-service sites, map onto CONVERSION-RULES):
  Before/After Wipe (highest-converting trade element), Instant Estimate odometer, Magnetic
  Call CTA, scraper-resistant Decode-Phone, no-jump Soft Accordion FAQ.
- **Glassworks** (premium-aesthetic only — heavy blur, RULE 13 caveat): stained-glass
  buttons, prism edge, progressive frost, fluted glass, condensation wipe, shatter pane,
  jeweler's loupe, re-tintable pane.
- **Showpieces:** gravity variable-type, momentum dial, metaball menu, specular tilt card,
  elastic spring slider, gum-stretch tabs.

### Breaking these into reusable components
The originals above are **preserved, never edited**. `components/` holds each effect broken
out as a **generic, variable-driven snippet** (`{{placeholders}}` + RGB-triplet accents).
`components/_manifest.json` catalogs all 26 with their variables + status and is built to be
**batch-processed (delegate extraction to a cheaper LLM)** one at a time; `components/magnetic-cta.html`
is the worked exemplar of the pattern. Lift a finished component, set its vars, ship.

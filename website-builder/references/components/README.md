# Components — generic, variable-driven extractions

The two HTML files in `../` (`glow-glass-kit.html`, `off-catalog-components.html`) are the
**preserved Fable originals** — never edit or delete them. This folder holds each effect
broken out as a **self-contained, brandable component**: scoped CSS + minimal JS, a `:root`
variable block at the top, and `{{HANDLEBARS}}` placeholders where the original had
spray-foam demo content. Drop one into any site, set the vars, done.

## How to process the rest
`_manifest.json` lists all 26 components with the variables each needs and a `status`
(`pending` → `done`). It's built to be batch-processed one entry at a time — ideal to
**delegate to a cheaper LLM** (token discipline): "extract `<slug>` from its source file
into `components/<slug>.html` following the convention block + the `magnetic-cta.html`
exemplar; replace all client content with the listed `{{vars}}`; keep the reduced-motion
guard." Then flip its status to `done`.

## Pattern (see `magnetic-cta.html`)
- **Colors → CSS custom props as RGB triplets** (`--accent: 255 180 84`) so
  `rgb(var(--accent) / <alpha>)` builds any tint from one knob.
- **Client content → `{{PLACEHOLDERS}}`** documented in the leading comment.
- **Conversion-relevant components** (`conversion_safe:true` + `conversion_note` in the
  manifest) carry a RULE 12 note — e.g. the magnetic CTA / decode-phone must wrap a real
  `tel:` link, not replace it.
- Keep `@media (prefers-reduced-motion: reduce)`.

## Conversion workhorses (highest business value — extract these first)
`before-after-wipe` · `instant-estimate` · `magnetic-cta` ✅ · `decode-phone` ·
`soft-accordion` — these map directly onto the CONVERSION-RULES and are safe on
home-service sites. The Glassworks set is premium-aesthetic only (heavy `backdrop-filter`
blur hurts mobile PageSpeed — see RULE 13).

# Phase 1 — Setup

**Goal:** resolve inputs, derive the slug, build the staging directory tree. Zero research yet.

## Steps

1. **Resolve inputs** (see SKILL.md → Inputs). Required: `topic`, `target_keyword`, `site_root`.
   Apply defaults for `blog_dir` (`content/blog`), `work_dir`
   (`<site_root>/ai/knowledge/article-research`), `location` (`United States`),
   `word_target` (`3500-5000`). Resolve `brand` / `site_author` / `site_url` from the site's
   config or `profile.md`; if genuinely unknown, ask ONCE here (this is the only acceptable
   pre-flight question) — never carry a `{{placeholder}}` into output.

2. **Derive the slug** — lowercase, hyphenated, SEO-friendly, from `target_keyword` (preferred)
   or `topic`. Strip stop-punctuation. Example: topic "Best CRM for small teams" → `best-crm-for-small-teams`.

3. **Create the directory tree:**
   ```bash
   SLUG="<slug>"; BASE="<work_dir>/$SLUG"
   mkdir -p "$BASE"/{topic-research,keyword-research,authority-link-research,internal-link-research,faq-research}
   mkdir -p "$BASE"/{article-outline-planner,article-design/images,schema-markup,extra-components,drafts}
   ```

4. **Seed `research-summary.md`** with the title, slug, target keyword, brand, and a "Phase 1
   complete — ready for research" marker.

## Output / hand-off
Directory tree exists; `research-summary.md` stub written. **Immediately proceed to Phase 2** —
do not stop or ask.

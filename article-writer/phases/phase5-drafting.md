# Phase 5 — Drafting

**Agent:** article-draft-agent (or handle directly). **Inputs:** outline + all research.
**Output:** `article-draft.md` (+ `drafts/draft-v1.md`).

## Requirements
- Follow the Phase-4 outline exactly.
- Hit `word_target` (default 3500-5000 words).
- Weave in all research findings; natural keyword integration (no stuffing).
- Include the FAQ section (8-12 Qs).
- Citations as markdown links `[text](url)` to validated authority sources.
- Engaging, readable, benefit-focused — no fear/scare-tactic framing.

## Frontmatter (GENERIC — resolved from inputs, never a hardcoded name)
```markdown
---
title: <SEO title>
description: <meta description>
keywords: <primary, secondary keywords>
author: <site_author>        # resolved input — NOT a hardcoded business name
brand: <brand>               # resolved input
date: <ISO date>
---
```

> The original hardcoded a specific agency byline here. Do NOT. Use the `site_author` / `brand`
> inputs. A draft that ships with a placeholder or a wrong/borrowed byline is a failure.

**Immediately launch Phase 6** (the 3 parallel enhancement agents). Token budget is not a reason
to stop.

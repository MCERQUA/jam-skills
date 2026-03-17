# Design Planning — Phase 4: The Thinking Phase

This is where the site goes from "another template" to a website that WORKS. You have the research. Now THINK through every design decision with intention.

**Do NOT skip this phase.** Do NOT say "I'll figure it out while coding." Every section, every color, every animation should have a REASON traced back to the research.

**Time investment:** 20-30 minutes of deliberate planning.
**Output directory:** `ai/design/`
**Prerequisite:** ALL research tasks complete (Phase 3).

---

## Step 1: Competitor Visual Audit

**Output:** `ai/design/competitor-visual-audit.md`

Go back through every competitor site review from `ai/research/03-competitor-analysis/site-reviews/`. This time you're looking at VISUAL patterns, not content.

### Document:

```markdown
# Competitor Visual Audit

## Layout Patterns

### Hero Sections
| Competitor | Hero Type | Image/Video | CTA Count | Layout |
|-----------|-----------|-------------|-----------|--------|
| [name] | Full-width image + overlay text | Stock photo of [subject] | 2 (form + phone) | Text left, image right |
| [name] | Split (text left, form right) | None — solid gradient | 1 (form embedded) | 50/50 split |
| [name] | Video background | Autoplay drone footage | 1 (button) | Centered text overlay |

**Pattern:** Most competitors use [X]. The most visually striking uses [Y].
**Opportunity:** [What would be better/different]

### Section Ordering (homepage)
Most common flow:
1. Hero — [X of Y competitors]
2. Trust bar — [X of Y]
3. Services/Features — [X of Y]
4. [Section] — [X of Y]
...

**What works about this order:** [Why this flow makes sense for the customer journey]
**What we should change:** [Where we can improve the flow]

### Navigation
| Style | Count | Example |
|-------|-------|---------|
| Standard horizontal navbar | X | [competitor] |
| Sticky navbar | X | [competitor] |
| Hamburger on desktop | X | [competitor] |
| Mega menu | X | [competitor] |

### Footer
Common footer elements:
- [element] — X competitors
- [element] — X competitors

## Color Patterns
| Competitor | Primary | Secondary | Accent | Background | Overall Feel |
|-----------|---------|-----------|--------|------------|-------------|
| [name] | [color] | [color] | [color] | [dark/light] | [corporate/modern/etc] |
| [name] | [color] | [color] | [color] | [dark/light] | [feel] |

**Niche color trends:** [What colors dominate this industry and why]
**Opportunity:** [How to stand out while still feeling "right" for the industry]

## Typography
| Competitor | Heading Font | Body Font | Max Heading Size | Density |
|-----------|-------------|-----------|-----------------|---------|
| [name] | [font] | [font] | [size] | [dense/airy] |

**Niche type trends:** [What typography choices are common]

## Animation & Motion
| Competitor | Entrance Animations | Scroll Effects | Hover States | Overall Motion Level |
|-----------|-------------------|---------------|-------------|---------------------|
| [name] | [none/fade/slide] | [none/parallax/reveal] | [basic/rich] | [low/medium/high] |

**Motion gap:** Most competitors use [level]. We can differentiate with [approach].

## Photography & Imagery
| Competitor | Image Style | Custom or Stock | Quality |
|-----------|------------|-----------------|---------|
| [name] | [real photos/illustrations/icons] | [custom/stock] | [high/medium/low] |

**Visual quality gap:** [Where competitors are weak visually]

## Overall Visual Ranking
Rank all competitors by visual quality:
1. [Best] — Why: [what makes them best]
2. [Second] — Why:
3. ...
X. [Worst] — Why: [what makes them worst]

**Our target:** Beat #[N] in visual quality. Specifically by: [how]
```

---

## Step 2: Style Direction

**Output:** `ai/design/style-direction.md`

Based on the visual audit, the brand intake, and the industry, make DELIBERATE style decisions.

### Document:

```markdown
# Style Direction: [Business Name]

## Aesthetic Choice
**Style:** [e.g., "Modern Professional with Warm Accents"]

**Why this style:**
- Industry context: [e.g., "Service businesses in this niche are all corporate blue. Warm accents will stand out while still feeling trustworthy."]
- Brand alignment: [e.g., "Client described their tone as 'friendly but professional' — this maps to clean lines with human warmth."]
- Competitor gap: [e.g., "Every competitor looks the same — dark blue, white text, stock photos. We're going dark mode with amber accents and custom illustrations."]

## Color Palette (with reasoning)
| Role | Color | Hex | Why |
|------|-------|-----|-----|
| Primary | [name] | [hex] | [reason — ties to industry/brand/differentiation] |
| Secondary | [name] | [hex] | [reason] |
| Accent | [name] | [hex] | [reason — used for CTAs, must contrast] |
| Background | [name] | [hex] | [reason — dark/light mode decision] |
| Text | [name] | [hex] | [reason — readability] |
| Muted | [name] | [hex] | [reason — secondary text, borders] |

## Typography (with reasoning)
| Role | Font | Weight | Why |
|------|------|--------|-----|
| Headings | [font] | [weight] | [reason — matches tone, readable, unique vs competitors] |
| Body | [font] | [weight] | [reason — readability at scale] |
| Accent (optional) | [font] | [weight] | [reason — for callouts, stats, special elements] |

## Photography Direction
- **Style:** [real photography / illustrations / mixed / icons-only]
- **Subject matter:** [what images should show — e.g., "completed projects, happy customers, team at work"]
- **Treatment:** [full color / desaturated / duotone / with overlays]
- **Sourcing:** [AI-generated / stock / client-provided / placeholder for now]

## Dark vs Light Mode
- **Default:** [dark / light]
- **Reasoning:** [e.g., "Dark mode — competitors are all light, dark feels more premium, better contrast for accent colors"]
- **Toggle available:** [yes / no]

## Spacing & Density
- **Overall feel:** [airy/spacious / balanced / dense/compact]
- **Section padding:** [generous py-24+ / standard py-16 / tight py-8]
- **Why:** [e.g., "Spacious — luxury feel, lets content breathe, differentiates from cluttered competitor sites"]
```

---

## Step 3: Component Plan

**Output:** `ai/design/component-plan.md`

Map every component needed for the site. For each one, define WHAT it does, WHY it's there, and HOW it should look.

### Document:

```markdown
# Component Plan: [Business Name]

## Homepage Components (in order)

### 1. Navbar
- **Type:** [sticky / standard / transparent-to-solid on scroll]
- **Items:** [Logo, Home, About, Services dropdown, Blog, Contact, CTA button]
- **CTA in nav:** [yes — "[CTA text]", [accent color] button]
- **Mobile:** [hamburger menu / bottom nav / slide-out]
- **Why this approach:** [reason from competitor analysis]

### 2. Hero
- **Type:** [full-width / split / centered / with form]
- **Layout:** [describe: "Text left with H1 + subtitle + 2 CTAs. Right side: angled image of [subject]. Gradient overlay on background."]
- **H1:** "[Exact headline from content plan]"
- **Subtitle:** "[1-2 sentences, benefit-focused]"
- **Primary CTA:** "[text]" → [destination]
- **Secondary CTA:** "[text]" → [destination]
- **Background:** [gradient / image / video / pattern]
- **Animation:** [entrance type — e.g., "Text fades up, image slides in from right, CTA buttons stagger in"]
- **Why this layout:** [reason — e.g., "Split layout outperformed full-width in competitor analysis. Form-in-hero captures leads immediately."]
- **Reference:** [which competitor has the best hero, what we're taking from it]

### 3. Trust Bar
- **Elements:** [list 4-6 trust signals from conversion research]
  - [e.g., "Licensed & Insured", "20+ Years Experience", "500+ Projects", "5-Star Reviews"]
- **Style:** [logo strip / icon + text / badges / stat counters]
- **Animation:** [counter animation for numbers / logo scroll / fade in]
- **Why these signals:** [from trust signal research — these are what matter in this industry]

### 4. [Next Section]
... [continue for every section on every page]

## Section Purpose Map

Every section must serve one of these roles:
| Role | Section | What It Does |
|------|---------|-------------|
| **Hook** | Hero | Capture attention, communicate value, CTA |
| **Trust** | Trust Bar, Testimonials | Prove credibility |
| **Educate** | Features, How It Works | Explain what you offer |
| **Differentiate** | Why Choose Us, Stats | Stand out from competition |
| **Answer** | FAQ | Remove objections, target long-tail SEO |
| **Convert** | CTA, Contact Form | Drive the action |

**Rule:** The page should flow: Hook → Trust → Educate → Differentiate → Answer → Convert

## Pages Summary

| Page | Section Count | Key Sections | Unique Elements |
|------|-------------|--------------|-----------------|
| Homepage | [N] | Hero, Trust, Features, How It Works, Testimonials, FAQ, CTA | [what makes it special] |
| About | [N] | Hero, Story, Values/Mission, Team, CTA | [what makes it special] |
| Services | [N] | Hero, Service Grid, Detail Sections, CTA | [what makes it special] |
| Contact | [N] | Hero, Form, Map/Info, FAQ | [what makes it special] |
```

---

## Step 4: Animation & Motion Plan

**Output:** `ai/design/animation-plan.md`

Motion is what separates a "regular" site from one that feels alive. But motion must be INTENTIONAL — every animation has a purpose.

### Document:

```markdown
# Animation Plan

## Motion Philosophy
**Overall level:** [subtle / moderate / rich]
**Why:** [reason — e.g., "Rich motion — competitors are all static. This is our biggest visual differentiator."]

## Entrance Animations
| Element | Animation | Duration | Delay | Trigger |
|---------|-----------|----------|-------|---------|
| Hero H1 | Fade up + slight scale | 0.6s | 0s | Page load |
| Hero subtitle | Fade up | 0.5s | 0.2s | Page load |
| Hero CTAs | Fade up | 0.4s | 0.4s | Page load |
| Section headings | Fade up | 0.5s | 0s | Scroll into view |
| Feature cards | Stagger fade up | 0.4s each | 0.1s stagger | Scroll into view |
| Stats numbers | Count up | 1.5s | 0s | Scroll into view |
| Testimonial cards | Slide in from sides | 0.5s | 0.15s stagger | Scroll into view |

## Hover Interactions
| Element | Hover Effect | Purpose |
|---------|-------------|---------|
| CTA buttons | Scale up 1.05 + shadow increase | Invites click |
| Feature cards | Lift up (translateY -4px) + shadow | Shows interactivity |
| Nav links | Underline slide in from left | Navigation feedback |
| Images | Slight scale 1.02 + brightness | Visual engagement |
| Social icons | Scale + color change | Interaction feedback |

## Scroll Effects
| Effect | Where | Description |
|--------|-------|-------------|
| Parallax background | Hero section | Background image moves at 0.5x scroll speed |
| Sticky section | [if applicable] | [description] |
| Progress indicator | [if applicable] | [description] |

## Continuous Animations (use sparingly)
| Element | Animation | Purpose |
|---------|-----------|---------|
| [e.g., gradient orbs] | Slow float/pulse | Background visual interest |
| [e.g., logo strip] | Infinite scroll marquee | Show partner/certification logos |

## Performance Rules
- All animations respect `prefers-reduced-motion`
- No animation longer than 1s (except counters)
- Stagger delays max 0.15s between items
- Use `will-change` on animated elements
- Disable parallax on mobile
```

---

## Step 5: Page Wireframes

**Output:** `ai/design/page-wireframes.md`

For each page, document the exact section-by-section layout. This is the blueprint you follow during build.

### Document:

```markdown
# Page Wireframes

## Homepage

### Section 1: Navbar [sticky, transparent → solid on scroll]
┌─────────────────────────────────────────────────┐
│ [Logo]   Home  About  Services▾  Blog  Contact  │ [Get Quote ➜]
└─────────────────────────────────────────────────┘

### Section 2: Hero [full-width, dark gradient bg]
┌─────────────────────────────────────────────────┐
│                                                   │
│  [H1: "Exact Headline Text"]          [IMAGE]    │
│  [Subtitle: 1-2 sentences]                       │
│                                                   │
│  [■ Primary CTA]  [○ Secondary CTA]             │
│                                                   │
└─────────────────────────────────────────────────┘
Animation: Text fades up, image slides in right

### Section 3: Trust Bar [py-6, muted bg]
┌─────────────────────────────────────────────────┐
│  ✓ Signal 1   │  ✓ Signal 2   │  ✓ Signal 3   │  ✓ Signal 4  │
└─────────────────────────────────────────────────┘

### Section 4: [Features / Services] [py-24]
┌─────────────────────────────────────────────────┐
│         [Section H2: "Keyword-rich heading"]      │
│         [Subtitle paragraph]                      │
│                                                   │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │ Icon │  │ Icon │  │ Icon │  │ Icon │        │
│  │Title │  │Title │  │Title │  │Title │        │
│  │ Desc │  │ Desc │  │ Desc │  │ Desc │        │
│  └──────┘  └──────┘  └──────┘  └──────┘        │
└─────────────────────────────────────────────────┘
Animation: Cards stagger in on scroll, lift on hover

[... continue for EVERY section on EVERY page ...]
```

---

## Step 6: Design Brief (Master Document)

**Output:** `ai/design/design-brief.md`

This is the SINGLE DOCUMENT that captures all design decisions. Reference this throughout the build phase.

```markdown
# Design Brief: [Business Name]

## Project Summary
- **Business:** [name] — [one-line description]
- **Site type:** [SEO Leadgen / Local Service / Portfolio / SaaS]
- **Primary goal:** [what visitors should do]
- **Target audience:** [who]

## Design Decisions Summary

### Visual Identity
- **Style:** [aesthetic name]
- **Colors:** [primary] / [secondary] / [accent]
- **Fonts:** [heading font] + [body font]
- **Mode:** [dark / light]
- **Spacing:** [airy / balanced / dense]

### What Makes This Site "Pop"
1. [Differentiator 1 — e.g., "Rich scroll animations — every competitor is static"]
2. [Differentiator 2 — e.g., "Dark mode with amber accents — everyone else is white/blue"]
3. [Differentiator 3 — e.g., "Real data in trust bar — not vague claims"]
4. [Differentiator 4 — e.g., "Comprehensive FAQ targeting 12 long-tail keywords"]
5. [Differentiator 5 — e.g., "Interactive service cards with hover reveals"]

### Why It Works (connecting research to design)
- **Keyword "[primary keyword]"** → H1 headline, meta title, first paragraph
- **Competitor gap: [gap]** → We address this with [section/element]
- **Trust signal research** → [specific trust elements] prominently placed
- **CTA pattern "[winning pattern]"** → Used as primary CTA throughout
- **Conversion funnel** → Page flow follows: Hook → Trust → Educate → Answer → Convert

## Page Count
- [N] pages total
- [N] homepage sections
- [N] total components needed

## Build Priorities
1. Homepage (establishes all patterns)
2. [Second priority page]
3. [Third priority page]
...

## Quality Bar
This site must:
- [ ] Look better than [best competitor from visual audit]
- [ ] Load faster than any competitor (Lighthouse Performance ≥ 90)
- [ ] Have more specific, keyword-targeted content
- [ ] Have real trust signals, not generic claims
- [ ] Have motion/animation that competitors lack
- [ ] Have comprehensive FAQ targeting long-tail keywords
- [ ] Pass all quality checks from `quality-checklist.md`
```

---

## What This Phase Prevents

Without this phase, you get:
- Generic hero sections with "Welcome to Our Business"
- Random color choices unrelated to the industry
- Sections in whatever order the template had
- No animations because "I'll add them later" (you won't)
- CTAs that say "Contact Us" instead of what actually works
- Trust signals that don't match what this industry's customers care about
- A site that looks like every other site in the niche

With this phase, you get:
- Every section justified by research
- Colors chosen to differentiate from competitors
- Section ordering that follows the conversion funnel
- Animation plan ready to implement
- CTAs tested against competitor patterns
- Trust signals that this industry's customers actually look for
- A site that stands out because every decision was intentional

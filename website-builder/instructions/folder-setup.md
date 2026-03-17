# Website AI Folder Setup — Phase 2

Every website project begins with a structured `/ai/` directory. This is where ALL research, design thinking, and content planning lives BEFORE any code gets written.

---

## Create the Structure

Run this at the start of every new website project. Path: `Websites/<project-name>/ai/`

```
ai/
├── research/
│   ├── 01-business-profile/
│   │   └── profile.md              ← Business info from intake (auto-filled)
│   ├── 02-keyword-research/
│   │   ├── primary-keywords.md     ← 3-5 high-volume core terms
│   │   ├── secondary-keywords.md   ← 10-20 service/feature terms
│   │   ├── longtail-keywords.md    ← 15-30 question/how-to phrases
│   │   ├── location-keywords.md    ← Geographic modifiers (if local)
│   │   └── keyword-clusters.md     ← Keywords grouped by topic/intent
│   ├── 03-competitor-analysis/
│   │   ├── competitor-list.md      ← Top 5-10 competitors identified
│   │   ├── site-reviews/           ← Per-competitor deep review files
│   │   │   ├── competitor-1.md
│   │   │   ├── competitor-2.md
│   │   │   └── ...
│   │   ├── pattern-analysis.md     ← Common patterns across all competitors
│   │   └── gaps-opportunities.md   ← What they all miss / do poorly
│   ├── 04-content-strategy/
│   │   ├── page-plan.md            ← Every page mapped: URL, keywords, sections, H1
│   │   ├── content-briefs/         ← Per-page detailed content specs
│   │   │   ├── homepage.md
│   │   │   ├── about.md
│   │   │   ├── services.md
│   │   │   └── ...
│   │   └── faq-research.md         ← Real questions from PAA, forums, Reddit
│   ├── 05-topical-map/
│   │   ├── topical-map.md          ← Full topic cluster architecture
│   │   ├── pillar-pages.md         ← Core pillar page definitions
│   │   └── cluster-pages.md        ← Supporting content mapped to pillars
│   ├── 06-local-seo/
│   │   ├── service-areas.md        ← Target cities/regions with keywords
│   │   ├── local-competitors.md    ← Location-specific competitor data
│   │   └── local-content-plan.md   ← City pages, area-specific content
│   └── 07-conversion-patterns/
│       ├── cta-analysis.md         ← What CTAs competitors use, what works
│       ├── trust-signals.md        ← Common trust elements in the niche
│       ├── social-proof.md         ← Review/testimonial patterns
│       └── conversion-funnel.md    ← Visitor journey: land → trust → convert
│
├── design/
│   ├── competitor-visual-audit.md  ← Visual patterns across competitor sites
│   ├── style-direction.md          ← Chosen aesthetic with reasoning
│   ├── component-plan.md           ← Every component needed, purpose, priority
│   ├── page-wireframes.md          ← Section-by-section layout per page
│   ├── animation-plan.md           ← Motion strategy: what moves, why, how
│   └── design-brief.md             ← MASTER doc: the complete design rationale
│
├── content/
│   ├── homepage-copy.md            ← All homepage text, written and reviewed
│   ├── about-copy.md
│   ├── services-copy.md
│   ├── contact-copy.md
│   └── ...                         ← One file per page
│
├── blog-research/
│   └── <slug>/                     ← Per-article research (Phase 7+)
│       ├── research/
│       ├── drafts/
│       └── final/
│
└── research-status.json            ← Tracks completion of each research phase
```

---

## Initialize research-status.json

```json
{
  "project": "<project-name>",
  "client": "<client-username>",
  "created": "<ISO-date>",
  "phases": {
    "business-profile": { "status": "not_started", "files": 0 },
    "keyword-research": { "status": "not_started", "files": 0 },
    "competitor-analysis": { "status": "not_started", "files": 0 },
    "content-strategy": { "status": "not_started", "files": 0 },
    "topical-map": { "status": "not_started", "files": 0 },
    "local-seo": { "status": "not_started", "files": 0 },
    "conversion-patterns": { "status": "not_started", "files": 0 },
    "design-plan": { "status": "not_started", "files": 0 },
    "content-writing": { "status": "not_started", "files": 0 }
  }
}
```

Update status values to `in_progress` or `complete` as you work through each phase. Update `files` count.

---

## Initialize Business Profile

Immediately after creating the folder structure, populate `01-business-profile/profile.md` with everything known from the intake conversation:

```markdown
# Business Profile: [Business Name]

## Identity
- **Business Name:**
- **Industry/Niche:**
- **One-line Description:**
- **Year Established:**
- **Location:**
- **Service Area:**

## Target Customer
- **Who:**
- **Problems they have:**
- **What they search for:**

## Services/Products
1. [Service] — [brief description]
2. ...

## Brand
- **Colors:** [hex codes or preferences]
- **Tone:** [professional/friendly/bold/playful/luxury/technical]
- **Logo:** [yes/no, description]

## Goals
- **Primary CTA:** [what visitors should do]
- **SEO Goals:** [what they want to rank for]
- **Known Competitors:** [URLs if provided]

## Site Type
- **Type:** [SEO Leadgen / Local Service / Portfolio / SaaS]
- **Pages Needed:** [list]
- **Special Features:** [list]

## Notes
[Any other relevant context from the conversation]
```

---

## Rules

1. **Create the FULL structure upfront.** Empty directories are fine — they mark what research is needed.
2. **Never skip the structure.** Even if the client says "just make me a simple site" — the research makes simple sites GOOD.
3. **Profile first.** The business profile drives every research task. Fill it before moving to Phase 3.
4. **Status tracking is mandatory.** Update `research-status.json` as you complete each section. This lets you resume if interrupted.
5. **All research files are markdown.** Easy to read, easy to reference during build.

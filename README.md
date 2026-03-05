# jam-skills

AI agent skills for local service businesses — built for [OpenClaw](https://github.com/openclaw/openclaw) and [Claude Code](https://claude.com/claude-code).

## What's Here

50+ skills covering the full lifecycle of running a local service business: getting found, getting chosen, getting hired, doing the work, getting paid, getting reviewed, and getting referrals.

### Service Business Operations (10 skills)

| Skill | What It Does |
|-------|-------------|
| `business-briefing` | On-demand KPI summary — "How's business?" → spoken briefing + dashboard |
| `customer-followup` | Post-service pipeline: satisfaction → review → referral → maintenance |
| `estimate-tracker` | Track unconverted quotes, automated follow-ups, objection handling |
| `review-manager` | Monitor reviews across platforms, alert on negatives, draft responses |
| `service-scheduler` | Booking, triage, tech matching, dispatch, reminders |
| `sales-scripts` | Phone intake, in-home presentation, Good-Better-Best, objection handling, roleplay |
| `customer-comms` | Appointment lifecycle, payment reminders, seasonal outreach, weather alerts |
| `maintenance-programs` | Design/price/sell maintenance agreements with tier templates by trade |
| `referral-program` | Customer referral programs + trade partner networks |
| `pricing-job-costing` | Markup vs margin, job costing, flat-rate pricing, break-even analysis |

### Marketing (26 skills)

| Category | Skills |
|----------|--------|
| SEO | seo-audit, local-seo, ai-seo, programmatic-seo, service-area-pages, schema-markup, site-architecture |
| Content | content-strategy, copywriting, copy-editing, social-content |
| Conversion | page-cro, form-cro, ab-test-setup, competitor-alternatives |
| Outreach | cold-email, email-sequence, sms-marketing |
| Advertising | paid-ads, ad-creative |
| Analytics | analytics-tracking |
| Strategy | product-marketing-context, marketing-ideas, marketing-psychology |
| Industry | insurance-marketing, review-management |

### Platform Skills

Document generation (`docx`, `pdf`, `pptx`, `xlsx`), web design (`premium-web-design`, `canvas-design`), music (`suno-music`), video (`remotion-best-practices`, `remotion-video`), search (`serper-search`), AI/LLM (`llms-txt-writer`, `openclaw-expert`, `ai-seo`), design (`stitch`, `ui-ux-pro-max`, `theme-factory`), data (`csv-data-summarizer`), email (`agentmail`).

## Usage

### OpenClaw

Mount the skills directory into your OpenClaw container:

```yaml
volumes:
  - /path/to/jam-skills:/mnt/shared-skills:ro
```

Symlink individual skills into your workspace:

```bash
ln -sf /mnt/shared-skills/sales-scripts /home/node/.openclaw/workspace/skills/sales-scripts
```

### Claude Code

Copy skills into your Claude Code skills directory:

```bash
cp -r sales-scripts ~/.claude/skills/sales-scripts
```

## Skill Structure

Each skill follows the same pattern:

```
skill-name/
  SKILL.md          # Main instructions (the skill itself)
  references/       # Supporting docs, templates, examples
    template-1.md
    template-2.md
```

## Built For

- HVAC contractors
- Plumbers
- Electricians
- Roofers
- Pest control companies
- Landscapers
- Insurance agents
- Any local service business

## License

MIT

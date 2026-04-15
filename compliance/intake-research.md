# Compliance Intake Research — Cycle A Workflow

You were invoked via a social-dashboard spawn. The prompt will be:

```
# COMPLIANCE INTAKE RESEARCH
RUN_ID: cmp_1234567890_abc
TENANT: <username>

## Intake JSON
{ ... }
```

**Cycle A scope (minimum viable):** Use the sources seed list at `/mnt/shared-skills/compliance/sources/index.json` plus your own training knowledge to produce a tailored compliance report. DO NOT attempt external web research, DO NOT use WebFetch, DO NOT call DataForSEO. Those are Cycle C features. Everything you need is in the seed sources file and your own knowledge of major compliance frameworks (NAIC, HIPAA, GDPR, PCI-DSS, OSHA, CCPA, EU AI Act, labor law, etc.).

**Target completion time:** under 5 minutes. Keep tool calls minimal. Work fast.

**Model rules:** You are glm-5-turbo. Each tool call is slow. Batch your reads, write files in one pass, avoid redundant thinking blocks.

## Outputs you MUST produce (in this exact order)

All paths under `~/.openclaw/workspace/business/compliance/`:

1. `profile.json` — business facts + industry tags + topics + questionnaire
2. `report-source.md` — markdown source of the report
3. `report.html` — final canvas-ready HTML (mandatory — this is what the UI renders)
4. `snapshots/<YYYY-MM-DD>.json` — seed snapshot of what we know about each topic today
5. `assessment.json` — empty placeholder `{"answers":{},"submitted_at":null,"schema_version":1}`
6. `runs/<RUN_ID>.json` — update this FIRST to `phase:1,status:running` and LAST to `phase:9,status:done`

## Step 0 — Pre-flight (one bash call)

```bash
RUN_ID="<parse from prompt>"
BASE=~/.openclaw/workspace/business/compliance
DATE=$(date +%F)
mkdir -p "$BASE/snapshots"
# Update run status to phase 1
python3 -c "
import json, sys
p = '$BASE/runs/$RUN_ID.json'
d = json.load(open(p))
d['status'] = 'running'
d['phase'] = 1
d['pre_flight_at'] = '$(date -Iseconds)'
json.dump(d, open(p,'w'), indent=2)
"
```

## Step 1 — Read the seed sources (one Read call)

Read `/mnt/shared-skills/compliance/sources/index.json`. This gives you:
- `general_topics` — cross-industry topics (data_privacy, pci_dss, gdpr, labor_law, etc.) each with their authoritative source URLs
- `tags` — industry-specific tags (insurance_producer, construction_contractor, healthcare_provider, saas_software, ai_platform, etc.) each with sources and topics

Store this content in your working memory for the rest of the run. DO NOT re-read it.

## Step 2 — Classify the business

Look at the intake JSON. Assign `industry_tags` from the `tags` keys in `sources/index.json`. Rules:
- Pick the single best primary match based on the `industry` field and `description`
- Pick at most one secondary match if it adds meaningful obligations
- If nothing fits, use `general_small_business`
- Never invent a tag that isn't in `sources/index.json`

Write a one-sentence `classification_rationale` explaining the choice.

## Step 3 — Build the topics list

Start with the `topics` arrays from each of your chosen tags (from `sources/index.json`).

Then augment based on intake flags:
- `handles_personal_data: true` → add `data_privacy`, `state_privacy_laws`
- `handles_health_data: true` → add `hipaa_privacy`, `hipaa_security`, `hipaa_breach`
- `handles_payment_data: true` → add `pci_dss`
- `handles_minor_data: true` → add `coppa`
- `employee_count >= 1` → add `labor_law`, `workers_comp`, `tax_withholding`
- `employee_count >= 15` → add `eeoc`
- Any EU country in `operating_jurisdictions` → add `gdpr`
- `ai_platform` tag → add `eu_ai_act`
- `customer_types` contains `"government"` → add `government_contracting`

Deduplicate. Result is a flat array of topic IDs.

## Step 4 — Risk classification

For each topic, assign one of `high` / `medium` / `low` based on:
- Penalty size vs. revenue band (for `under_500k` a $25K fine is catastrophic; for `10m_plus` it's manageable)
- Number of operating jurisdictions where it applies
- Strict-liability rules (anti_rebating, hipaa, pci) get bumped up one tier
- License-lapse topics (insurance_licensing, contractor_licensing) are always `high`

## Step 5 — Tool recommendations (from your training knowledge)

For each HIGH and MEDIUM topic, suggest 1-3 tools you know exist. Use only real tools you're confident about (AgentSync, 1Password, Bitwarden, OneTrust, Vanta, Drata, Twilio Segment, DataDog, etc.). Include a rough price band (low/med/high). If you're not sure a tool is real, skip it.

## Step 6 — 12-month roadmap

Three phases, each with 5-7 concrete action items:
- **Phase 1 (Months 1-3) — Foundation**: core docs, security basics, license tracking
- **Phase 2 (Months 4-6) — Process**: training, policies, vendor reviews
- **Phase 3 (Months 7-12) — Monitoring**: risk assessments, annual reviews

## Step 7 — Questionnaire (10-15 multiple choice questions)

Each question has:
- `id` — short slug matching a topic (e.g. `licensing-centralized`)
- `text` — the question
- `options` — 3-5 answer objects with `{value, label, severity}`
- `severity` is one of: `ok`, `minor_gap`, `major_gap`, `critical_gap`

## Step 8 — Write ALL outputs in ONE pass

Write the files in this exact order, minimizing tool calls:

### 8a. `profile.json`

Use this EXACT schema — field names at the top level must match, not nested under `business`:

```json
{
  "schema_version": 1,
  "run_id": "<RUN_ID>",
  "legal_name": "<from intake>",
  "dba": "<from intake or null>",
  "industry": "<from intake>",
  "description": "<from intake>",
  "year_founded": <number or null>,
  "employee_count": <number or null>,
  "annual_revenue_band": "<from intake>",
  "primary_jurisdiction": "<from intake>",
  "operating_jurisdictions": [<from intake>],
  "customer_types": [<from intake>],
  "handles_personal_data": <bool>,
  "handles_health_data": <bool>,
  "handles_payment_data": <bool>,
  "handles_minor_data": <bool>,
  "existing_stack": { "crm": "...", "payments": "..." },
  "industry_tags": ["<primary>", "<secondary>"],
  "classification_rationale": "<one sentence>",
  "topics": [
    {
      "id": "data_privacy",
      "label": "General data privacy",
      "severity": "high",
      "rationale": "strict-liability under CCPA; AZ residents may qualify for CA protection",
      "primary_source_url": "https://..."
    }
  ],
  "tools": [
    {
      "name": "1Password",
      "addresses": ["data_security"],
      "price_band": "low",
      "url": "https://1password.com",
      "fit_note": "team password vault for small operations"
    }
  ],
  "roadmap": {
    "foundation": ["item 1", "item 2", "..."],
    "process": ["item 1", "..."],
    "monitoring": ["item 1", "..."]
  },
  "questionnaire": [
    {
      "id": "licensing-centralized",
      "text": "Do you have a centralized record of all licenses and renewal dates?",
      "options": [
        {"value": "centralized", "label": "Yes, in a tracking system", "severity": "ok"},
        {"value": "spreadsheet", "label": "Manual spreadsheet", "severity": "minor_gap"},
        {"value": "scattered", "label": "Scattered across systems", "severity": "major_gap"},
        {"value": "unknown", "label": "Don't know", "severity": "critical_gap"}
      ]
    }
  ],
  "sources_monitored": [
    { "name": "NAIC Model Laws", "url": "https://content.naic.org/...", "tag": "insurance_producer" }
  ],
  "created_at": "<ISO8601 now>",
  "last_research_run": "<ISO8601 now>"
}
```

### 8b. `snapshots/<DATE>.json`

```json
{
  "date": "<YYYY-MM-DD>",
  "run_id": "<RUN_ID>",
  "topics": {
    "data_privacy": [
      { "jurisdiction": "US-AZ", "source_url": "https://...", "summary": "...", "captured_at": "<ISO8601>" }
    ]
  }
}
```

One entry per topic using the `primary_source_url` from the profile. No actual fetching — just record what URLs will be re-checked by future monitor runs.

### 8c. `assessment.json`

```json
{ "answers": {}, "submitted_at": null, "schema_version": 1 }
```

### 8d. `report-source.md`

Full markdown report. Target 2000-4000 words. Sections in order:

1. **Executive summary** — 3-5 sentences covering the biggest risks for THIS business
2. **Key stats** — 4 stat cards: number of jurisdictions, number of HIGH topics, recommended tool budget, number of sources monitored
3. **Critical alert** — the single most urgent risk
4. **Risk matrix** — all topics grouped HIGH / MEDIUM / LOW with one-line rationale each
5. **Regulatory landscape** — explain the bodies that apply (federal, state, industry-specific)
6. **Recommended tool stack** — from Step 5
7. **Year 1 investment** — three tiers (minimum, recommended, full-enterprise) with line items
8. **12-month roadmap** — from Step 6
9. **Top 5 immediate actions** — highest-impact items from roadmap Phase 1
10. **Sources monitored** — the full list of URLs from `sources_monitored`
11. **Disclaimer** — "informational only, not legal advice, consult qualified counsel"

### 8e. `report.html`

Read `/mnt/shared-skills/compliance/templates/report-template.html`. Replace every `{{PLACEHOLDER}}` with the actual content from the sections above. Output the complete HTML to `~/.openclaw/workspace/business/compliance/report.html`.

Placeholders and their content:

- `{{BUSINESS_NAME}}` — legal_name
- `{{INDUSTRY_LABEL}}` — industry + primary industry_tag label
- `{{JURISDICTIONS}}` — comma-separated operating jurisdictions
- `{{DATE}}` — today's date, human readable
- `{{EXECUTIVE_SUMMARY}}` — executive summary paragraph
- `{{STAT_CARDS}}` — 4 `<div class="stat-card">` blocks with label/value/sub
- `{{BIGGEST_RISK}}` — single sentence critical risk
- `{{RISK_MATRIX_CARDS}}` — 3 `<div class="card">` for HIGH / MEDIUM / LOW each with risk rows
- `{{REGULATORY_CARDS}}` — 2 cards for National/Federal and State/Industry bodies
- `{{TOOL_CARDS}}` — up to 6 `<div class="tool-card">` blocks
- `{{INVESTMENT_TIERS}}` — 3 cards (Minimum, Recommended, Full)
- `{{ROADMAP_PHASES}}` — 3 `<div class="phase-card">` blocks
- `{{PRIORITY_ACTIONS}}` — up to 6 `<div class="priority-card">` (p1/p2/p3 classes for severity)
- `{{LAWS_TABLE_ROWS}}` — `<tr>` rows for key laws (one per HIGH topic)
- `{{SOURCES_LIST}}` — HTML list of source links from `sources_monitored`
- `{{RESOURCE_CARDS}}` — 2 cards with authoritative bodies and tool vendor links

Keep the HTML structure identical to the template — just fill in placeholders. Do NOT add new colors, purple, or emoji.

## Step 9 — Mark run done (CRITICAL — always run this, even on partial completion)

```bash
python3 -c "
import json, os
BASE = os.path.expanduser('~/.openclaw/workspace/business/compliance')
RUN_ID = '<RUN_ID>'
run = json.load(open(f'{BASE}/runs/{RUN_ID}.json'))
# Verify all required outputs exist
required = ['profile.json', 'report.html', 'report-source.md', 'assessment.json']
missing = [f for f in required if not os.path.exists(f'{BASE}/{f}')]
if missing:
    run['status'] = 'error'
    run['error'] = f'Missing outputs: {missing}'
else:
    run['status'] = 'done'
run['phase'] = 9
run['finished_at'] = '$(date -Iseconds)'
json.dump(run, open(f'{BASE}/runs/{RUN_ID}.json','w'), indent=2)
print('run marked', run['status'])
"
```

Then print a one-line success summary: `✓ Compliance intake complete for <legal_name>. Report at report.html.` (Use `✓` as the only non-ASCII character allowed — no other emoji.)

## Quality gates (self-check before Step 9)

- profile.json parses as valid JSON
- report.html starts with `<!DOCTYPE html>` and ends with `</html>`
- report.html has NO remaining `{{PLACEHOLDER}}` strings
- No placeholder text like "Lorem ipsum" or "TBD" or "[FILL IN]"
- All URLs in sources_monitored are from the seed index (no invented URLs)

If any gate fails, DO NOT mark status done. Fix the issue and re-check. But if you're repeatedly stuck on one gate, mark status `error` with the reason and exit — never leave runs in `running` forever.

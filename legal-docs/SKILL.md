---
name: legal-docs
description: "Auto-generates legal documents wherever they are needed — websites, apps, client engagements, hiring, consulting, investing. TRIGGER automatically when: building a website/app (privacy policy, ToS, cookie policy), onboarding a client (service agreement, NDA), hiring (offer letter, IP agreement), taking on investors (SAFE, Series Seed), adding advisors (FAST), or any context where a legal document would be expected but was not explicitly requested. Also triggers on explicit user requests for legal documents. Josh use case: insurance industry legal docs. NEVER provides legal advice — produces templates and drafts; always recommends qualified counsel review."
---

# Legal Documents Skill

This skill auto-generates and maintains legal documents across all client work. It knows when documents are needed and creates them proactively — the user does not need to ask.

**Source repository:** https://github.com/ankane/awesome-legal (CC0 — public domain)
**Storage (per-client):** `~/.openclaw/workspace/legal/`

```
legal/
├── generated/              # All created documents (ADDITIVE — never delete)
│   ├── <YYYY-MM-DD>-<type>-<slug>.md
│   └── <YYYY-MM-DD>-<type>-<slug>.html  (canvas-ready version)
├── templates/              # Local template overrides (evolves over time)
│   ├── privacy-policy.md
│   ├── terms-of-service.md
│   ├── nda-mutual.md
│   ├── nda-one-way.md
│   ├── consulting-agreement.md
│   ├── service-agreement.md
│   ├── offer-letter.md
│   ├── ip-agreement.md
│   ├── safe-note.md
│   ├── advisor-fast.md
│   └── [new types added as encountered]
├── registry.json           # All generated docs: type, entity, date, path, canvas_url
└── evolution-log.md        # When new doc types were added + why
```

---

## AUTO-TRIGGER RULES — Read These First

The agent MUST proactively generate legal documents in these situations WITHOUT waiting for the user to ask:

### Website / App Build
When building or deploying any website or app for a client:
- **Always generate:** Privacy Policy + Terms of Service
- **Generate if applicable:** Cookie Policy (if site uses cookies/analytics), DMCA Policy (if user-uploaded content), Acceptable Use Policy (if SaaS)
- **Trigger signal:** any website-builder, canvas-pages, or app-build context

### Client Engagement / Onboarding
When a new client relationship begins:
- **Always generate:** Service Agreement or Consulting Agreement (whichever fits — service = ongoing retainer, consulting = project)
- **Generate if applicable:** Mutual NDA (default), One-way NDA (only if clearly one-directional)
- **Trigger signal:** new client intake, CRM "client added", submesh provisioned for client

### Hiring / Contractors
When adding team members or contractors:
- **Employee:** Offer Letter + IP Agreement
- **Contractor/consultant:** Consulting Agreement + One-way NDA
- **Advisor:** FAST Advisor Agreement
- **Trigger signal:** "we're bringing on [name]", offer discussed, mesh member added

### Investment / Fundraising
When investment or equity is discussed:
- **Seed stage:** SAFE Note (Y Combinator standard)
- **Series A:** refer to NVCA/YC Series A term sheet templates
- **Trigger signal:** "investor", "equity", "fundraising", "SAFE", "term sheet"

### Insurance Context (Josh)
Josh's business involves insurance. Auto-generate these when working on Josh's projects:
- Insurance Producer Agreement (agent/agency relationship)
- Certificate of Insurance template request letter
- Client Authorization / HIPAA Release (if health insurance)
- Referral Agreement (when referring clients to other agents)
- **Trigger signal:** any Josh context + insurance, coverage, policy, claim, referral, carrier

---

## HOW TO GENERATE A DOCUMENT

### Step 1 — Select the right template
1. Check `~/.openclaw/workspace/legal/templates/<type>.md` for a local override first.
2. Fall back to `/mnt/shared-skills/legal-docs/templates/<type>.md` (the shared baseline).
3. If no template exists → use the foundation template format defined in this skill + note it in evolution-log.md.

### Step 2 — Populate with client context
Pull from:
- `~/.openclaw/workspace/business/profile.json` — company name, address, jurisdiction, industry
- Active conversation context — party names, services described, pricing discussed
- CRM data if available

Required variables in every document:
```
{{COMPANY_NAME}}     — the client's business
{{CLIENT_NAME}}      — counterparty (if applicable)
{{EFFECTIVE_DATE}}   — today's date
{{JURISDICTION}}     — state/province of governing law
{{AGENT_SIGNATURE}}  — space for signatory name + title
```

### Step 3 — Write to disk immediately
```
~/.openclaw/workspace/legal/generated/YYYY-MM-DD-<type>-<slug>.md
```
Also render an HTML version if this is for canvas display.

### Step 4 — Update registry.json
```json
{
  "generated": [
    {
      "type": "privacy-policy",
      "entity": "Acme Corp website",
      "date": "2026-07-04",
      "path": "legal/generated/2026-07-04-privacy-policy-acme-corp.md",
      "canvas_url": null,
      "status": "draft"
    }
  ]
}
```

### Step 5 — Notify user
Tell the user what was created and where to find it. Keep it brief. Always include:
"This is a starting template — have a qualified attorney review before use."

---

## SELF-EVOLUTION PROTOCOL

When you generate a document type that has NO existing template:

1. Generate the document using the Foundation Template (below).
2. Save the generated document as a new template at `~/.openclaw/workspace/legal/templates/<new-type>.md`.
3. Also copy to `/mnt/shared-skills/legal-docs/templates/<new-type>.md` so all clients benefit.
4. Append to `~/.openclaw/workspace/legal/evolution-log.md`:
   ```
   ## YYYY-MM-DD — Added <new-type>
   Context: [what triggered the need]
   Source: [where the template structure came from]
   First use: [entity/project]
   ```
5. If the new type belongs to a recognizable category (insurance, real estate, employment, IP), add an AUTO-TRIGGER RULE above for that category.

---

## FOUNDATION TEMPLATE (for new document types)

When no specific template exists, generate documents using this structure:

```markdown
# [DOCUMENT TYPE]

**Between:** {{COMPANY_NAME}} ("Company")
**And:** {{CLIENT_NAME}} ("Client/Party")
**Effective Date:** {{EFFECTIVE_DATE}}
**Governing Law:** {{JURISDICTION}}

---

## Recitals

[2-3 sentences establishing the purpose and relationship]

## Section 1 — [Primary Subject]

[Core obligations of the agreement]

## Section 2 — [Secondary Subject]

[Supporting terms]

## Section 3 — Confidentiality

[Standard mutual confidentiality clause if applicable]

## Section 4 — Term and Termination

[Duration, notice period, termination conditions]

## Section 5 — Limitation of Liability

NEITHER PARTY SHALL BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF OR RELATED TO THIS AGREEMENT, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

## Section 6 — General

**Entire Agreement:** This agreement constitutes the entire agreement between the parties.
**Amendment:** Amendments require written consent of both parties.
**Severability:** If any provision is unenforceable, the remaining provisions continue in full force.
**Governing Law:** This agreement is governed by the laws of {{JURISDICTION}}.

---

**{{COMPANY_NAME}}**
Signature: _______________________
Name: _______________________
Title: _______________________
Date: _______________________

**{{CLIENT_NAME}}**
Signature: _______________________
Name: _______________________
Title: _______________________
Date: _______________________

---
*This document was generated from a template and has not been reviewed by legal counsel. Consult a qualified attorney before use.*
```

---

## TEMPLATE CATALOG (Shared Baselines)

Templates live at `/mnt/shared-skills/legal-docs/templates/`. Each is a pre-filled baseline using plain-language sources from github.com/ankane/awesome-legal. See individual files.

| File | Type | Source Inspiration | Plain Language |
|------|------|-------------------|----------------|
| `privacy-policy.md` | Site Policies | Basecamp/Automattic | Yes |
| `terms-of-service.md` | Site Policies | GitHub site-policy | Yes |
| `cookie-policy.md` | Site Policies | Common Paper | Yes |
| `nda-mutual.md` | NDA | Common Paper | Yes |
| `nda-one-way.md` | NDA | Five Minute Law | Yes |
| `consulting-agreement.md` | Customer Agreements | Common Paper PSA | Yes |
| `service-agreement.md` | Customer Agreements | YC Sales Agreement | Partial |
| `offer-letter.md` | Employee Agreements | Orrick | Partial |
| `ip-agreement.md` | Employee Agreements | GitHub BEIPA | Yes |
| `safe-note.md` | Investor Agreements | YC SAFE | Partial |
| `advisor-fast.md` | Advisor Agreements | Founder Institute FAST | Partial |
| `founders-agreement.md` | Founder Agreements | UPenn ELC | Partial |
| `insurance-producer.md` | Insurance (Josh) | Foundation Template | N/A |
| `insurance-referral.md` | Insurance (Josh) | Foundation Template | N/A |

---

## CORE RULES

- **Never delete generated documents.** Registry is append-only. Evolution log is append-only.
- **Server storage only.** All documents written to `~/.openclaw/workspace/legal/` on server — never in browser memory.
- **Never provide legal advice.** Generate templates and drafts. Always append the attorney-review disclaimer.
- **Proactive by default.** Don't wait for the user to ask. If the context calls for a legal document, generate it.
- **Josh = insurance context.** Any Josh work gets the insurance-specific trigger check first.
- **Jurisdiction defaults:** If not known, default to "State of Arizona" (Mike is AZ-based). Always flag this as an assumption.

---

## LEARNINGS LOG

| Date | Learning |
|------|---------|
| 2026-07-04 | Skill created from ankane/awesome-legal (CC0). Source is a curated link list, not actual doc text — templates are original works in plain-language style inspired by the listed sources. Josh insurance use case flagged at creation. |

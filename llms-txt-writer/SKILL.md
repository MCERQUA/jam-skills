---
name: llms-txt-writer
description: Comprehensive guide for creating effective llms.txt files that optimize websites for AI search engines and LLM discovery. Includes format specifications, best practices, industry examples, and testing strategies.
---

# LLMs.txt Writer Skill

**Purpose:** Create properly formatted `/llms.txt` files that maximize AI search visibility and enable large language models to effectively understand and navigate website content.

## What is llms.txt?

The `/llms.txt` standard addresses a critical challenge: **large language models struggle with context window limitations when accessing websites**. Traditional HTML pages contain navigation, ads, and JavaScript that complicate LLM comprehension.

**llms.txt provides:**
- Brief background information about your site
- Curated guidance for AI agents
- Links to detailed markdown files
- Optimized structure for inference-time assistance

**Key Benefit:** Instead of forcing LLMs to crawl entire sites, llms.txt centralizes essential information in a clean, parseable format.

---

## Core Format Specification

### Required Structure

```markdown
# Project or Website Name

> Brief summary with essential context (1-2 sentences)

Optional: Detailed paragraphs explaining the project, services, or content.
Use clear, concise language. Avoid jargon unless it's industry-standard.

## Section Name (e.g., "Docs" or "Key Pages")

- [Link Title](url): Brief description of what this resource contains
- [Another Page](url): What users will find here

## Optional

- [Extended Resource](url): Secondary information that can be skipped if context is limited
- [Additional Reading](url): Supplementary materials
```

### Critical Elements

1. **H1 Header** (Required): Your site/project name
2. **Blockquote** (Optional but recommended): 1-2 sentence summary
3. **Body Paragraphs** (Optional): Detailed explanation
4. **H2 Sections** (Optional): Organized file lists
5. **"Optional" Section** (Special): Content LLMs can skip when context is tight

---

## Best Practices for Effective llms.txt Files

### 1. Use Concise, Clear Language

**Good:**
```markdown
# Contractor's Choice Agency

> Insurance solutions for construction contractors specializing in high-risk trades like roofing, spray foam, and HVAC.

We provide specialized insurance coverage for contractors who face unique risks.
Our team understands trade-specific challenges and offers tailored policies.
```

**Bad:**
```markdown
# CCA

> We do insurance stuff.

Our company is the best at what we do and we've been doing it for years.
We offer various products and services to meet your needs.
```

### 2. Include Informative Link Descriptions

**Good:**
```markdown
## Insurance Products

- [Roofing Contractor Insurance](https://example.com/roofing): Coverage for slip-and-fall, property damage, and equipment
- [Spray Foam Insurance](https://example.com/spray-foam): Specialized policies for insulation contractors including pollution liability
```

**Bad:**
```markdown
## Products

- [Click here](https://example.com/page1)
- [Learn more](https://example.com/page2)
```

### 3. Organize Information Hierarchically

**Structure from essential → supplementary:**

```markdown
## Core Services
- [Main offerings](url): Primary products/services

## Resources
- [Guides](url): Educational content
- [FAQs](url): Common questions

## Optional
- [Blog Archive](url): Historical posts
- [Press Kit](url): Media resources
```

### 4. Provide Markdown Versions of Key Pages

The llms.txt standard expects markdown versions accessible by appending `.md`:

- `https://example.com/about.html` → `https://example.com/about.html.md`
- `https://example.com/` → `https://example.com/index.html.md`

**Implementation:**
- Generate markdown versions of key pages
- Store them alongside HTML versions
- Configure server to serve `.md` files with correct MIME type

---

## Industry-Specific Templates

### Insurance Agency

```markdown
# [Agency Name]

> Specialized insurance for [target market] serving [geographic area or industry].

We provide comprehensive coverage solutions for [specific niches]. Our team has [X] years
of experience helping [client type] protect their businesses.

## Insurance Products

- [Product 1](url): Coverage details and who it's for
- [Product 2](url): What this policy covers
- [Product 3](url): Key benefits and requirements

## Resources

- [Insurance Guide](url): Comprehensive guide to [topic]
- [Claims Process](url): Step-by-step claims filing
- [Risk Management](url): Tips for reducing insurance costs

## About

- [Our Team](url): Licensed agents and specialists
- [Service Areas](url): States and regions we serve
- [Contact](url): Phone, email, and office locations

## Optional

- [Blog](url): Industry news and insights
- [Case Studies](url): Client success stories
- [FAQ](url): Common insurance questions
```

### Restaurant

```markdown
# Franklin's BBQ

> Award-winning Texas BBQ in Austin, TX. Slow-smoked brisket, ribs, and traditional sides.

Established in 2009, Franklin's specializes in Central Texas-style barbecue using post oak wood
and 12-hour smoking processes.

## Menus

- [Lunch Menu](url.md): Available 11am-2pm daily
- [Dinner Menu](url.md): Available 5pm-9pm Fri-Sat
- [Catering](url.md): Full-service BBQ for events

## Information

- [Hours & Location](url.md): 11am-9pm, 900 E 11th St, Austin TX
- [Reservations](url.md): How to book a table
- [About Our Process](url.md): How we make our BBQ

## Optional

- [Press & Awards](url): Media coverage and accolades
- [Jobs](url): Current openings
```

### SaaS Product

```markdown
# FastHTML

> Build modern web applications using Python. No JavaScript required.

FastHTML is a Python framework for creating dynamic web apps with minimal code.
Uses HTMX for reactivity and Starlette for routing.

## Docs

- [Quick Start](url): Get started in 5 minutes
- [Core Concepts](url): Understanding FastHTML architecture
- [API Reference](url): Complete function documentation

## Examples

- [Todo App Tutorial](url): Build a full CRUD app
- [Authentication Example](url): User login and sessions
- [Database Integration](url): Working with SQLite and PostgreSQL

## Reference

- [HTMX Guide](url): HTMX integration patterns
- [Starlette Docs](url): Routing and middleware

## Optional

- [FastCore Library](url): Utility functions
- [Contributing Guide](url): How to contribute to FastHTML
```

### E-commerce/Retail

```markdown
# [Store Name]

> [Product category] for [target customer]. [Unique value proposition].

We specialize in [specific products] serving [customer segment]. Our inventory includes
[key categories] from [notable brands or origins].

## Shop

- [Product Category 1](url): [Number] items in stock
- [Product Category 2](url): New arrivals and bestsellers
- [Sale Items](url): Current promotions and discounts

## Customer Service

- [Shipping & Returns](url): Policies and timelines
- [Size Guide](url): Measurement charts
- [Contact Support](url): Phone, email, live chat

## About

- [Our Story](url): Company history and mission
- [Sustainability](url): Environmental commitments
- [Locations](url): Store addresses and hours

## Optional

- [Blog](url): Style guides and product news
- [Wholesale](url): B2B opportunities
```

---

## AI Search Visibility Optimization

### How llms.txt Improves Discoverability

1. **Centralized Information**: LLMs find curated content immediately
2. **Context Efficiency**: Structured format fits within context windows
3. **Agent Navigation**: AI assistants understand site architecture quickly
4. **Inference-Time Assistance**: Helps users actively seeking information
5. **Markdown Links**: Direct access to clean, parseable content

### SEO Keywords Strategy

**Include relevant keywords naturally:**

```markdown
# Arizona Roofing Insurance

> Commercial and residential roofing contractor insurance in Arizona.
Specialized coverage for Phoenix, Scottsdale, and Tucson roofers.

We provide comprehensive insurance solutions for Arizona roofing contractors including
general liability, workers compensation, and commercial auto coverage. Our policies
address unique risks like heat-related claims, monsoon damage, and tile roofing liability.

## Coverage Options

- [Commercial Roofing Insurance](url): Coverage for flat roof, TPO, and modified bitumen specialists
- [Residential Roofing Insurance](url): Policies for tile, shingle, and metal roof installers
- [Workers Compensation](url): Arizona workers comp for roofing crews
```

**Why this works:**
- Natural keyword placement (Arizona, roofing, insurance)
- Geographic specificity (Phoenix, Scottsdale, Tucson)
- Industry terminology (TPO, modified bitumen, tile roofing)
- Service keywords (workers compensation, general liability)
- Trade-specific language (flat roof, monsoon damage)

### Link Description Optimization

**Keyword-rich descriptions help AI understanding:**

```markdown
## Resources

- [Spray Foam Safety Guide](url): OSHA-compliant safety procedures for spray polyurethane foam contractors
- [Equipment Maintenance Checklist](url): Daily and weekly maintenance for Graco and PMC spray rigs
- [Insurance Cost Calculator](url): Estimate workers comp and GL premiums for foam insulation businesses
```

Each description includes:
- Primary keyword (safety, equipment, insurance)
- Industry terminology (OSHA, polyurethane foam, spray rigs)
- Brand names when relevant (Graco, PMC)
- Specific applications (cost calculator, checklist)

---

## Testing Your llms.txt File

### Manual Testing Checklist

**✓ Format Validation:**
- [ ] H1 header present at top
- [ ] Blockquote summary is 1-2 sentences
- [ ] All links use `[Text](url)` format
- [ ] "Optional" section clearly marked (if used)
- [ ] No unexplained jargon or acronyms
- [ ] Consistent punctuation in descriptions

**✓ Content Quality:**
- [ ] Links describe content clearly
- [ ] Organization flows logically
- [ ] Essential info appears before optional
- [ ] Industry keywords included naturally
- [ ] Contact/support info easy to find

**✓ Technical Requirements:**
- [ ] File located at `/llms.txt` (root of domain)
- [ ] Plain text UTF-8 encoding
- [ ] Markdown formatting correct
- [ ] All URLs absolute (include https://)
- [ ] Linked `.md` files exist and are accessible

### Automated Testing with LLMs

**Test with Claude or GPT:**

```python
import anthropic
import requests

# Fetch your llms.txt
response = requests.get("https://yourdomain.com/llms.txt")
llms_content = response.text

# Test with Claude
client = anthropic.Anthropic(api_key="your-key")
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"Here's a website's llms.txt file. Can you explain what this website does and what services it offers?\n\n{llms_content}"
    }]
)

print(message.content[0].text)
```

**What to verify:**
- LLM correctly identifies your site's purpose
- Key services/products are understood
- Important details aren't missed
- Navigation suggestions make sense

### Using llms_txt2ctx Tool

**Command-line validation:**

```bash
# Install tool
pip install llms-txt

# Generate context from your file
llms_txt2ctx https://yourdomain.com/llms.txt

# Generate full context (includes linked pages)
llms_txt2ctx https://yourdomain.com/llms.txt --full

# Save to file for review
llms_txt2ctx https://yourdomain.com/llms.txt > output.txt
```

**Review the output:**
- Is all essential information included?
- Are linked pages being fetched correctly?
- Does the full context stay under typical LLM limits?
- Is the markdown rendering properly?

---

## Implementation Guide

### Step 1: Create the File

1. Create `/llms.txt` in your website root
2. Start with H1 and blockquote
3. Add body paragraphs with key information
4. Organize links into logical sections
5. Add "Optional" section for supplementary content

### Step 2: Generate Markdown Versions

**For key pages, create `.md` versions:**

```bash
# Manual conversion
pandoc page.html -o page.html.md

# Or use a script
for file in *.html; do
    pandoc "$file" -o "$file.md" --wrap=none
done
```

### Step 3: Configure Server

**Nginx example:**

```nginx
location ~ \.md$ {
    types { }
    default_type text/markdown;
    add_header Content-Type "text/markdown; charset=utf-8";
}

location = /llms.txt {
    types { }
    default_type text/plain;
    add_header Content-Type "text/plain; charset=utf-8";
}
```

**Apache example:**

```apache
<FilesMatch "\.md$">
    ForceType text/markdown
    Header set Content-Type "text/markdown; charset=utf-8"
</FilesMatch>

<Files "llms.txt">
    ForceType text/plain
    Header set Content-Type "text/plain; charset=utf-8"
</Files>
```

### Step 4: Test and Iterate

1. Test with LLMs (Claude, GPT, Gemini)
2. Run `llms_txt2ctx` validation
3. Ask friends/colleagues to review
4. Monitor how AI agents interact with your site
5. Update based on feedback

### Step 5: Maintain and Update

**Regular maintenance:**
- Update when site structure changes
- Add new pages to appropriate sections
- Remove dead links
- Refine descriptions based on user questions
- Keep content current

---

## Common Mistakes to Avoid

### ❌ Vague Descriptions

```markdown
- [About](url): Learn about us
- [Services](url): What we do
```

**✅ Better:**

```markdown
- [About Our Team](url): Meet our licensed insurance agents specializing in contractor coverage
- [Insurance Services](url): General liability, workers comp, and commercial auto for contractors
```

### ❌ Missing Context

```markdown
# CCA

- [Products](url)
- [Contact](url)
```

**✅ Better:**

```markdown
# Contractor's Choice Agency

> Specialized insurance for construction contractors in Arizona.

We provide tailored coverage for high-risk trades including roofing,
spray foam insulation, and HVAC installation.

## Insurance Products

- [Roofing Insurance](url): Coverage for commercial and residential roofers
- [Contact Us](url): Phoenix office: 844-967-5247
```

### ❌ Unexplained Jargon

```markdown
- [TPO Coverage](url): For modified bitumen specialists
- [ISO Ratings](url): Understanding your ISO
```

**✅ Better:**

```markdown
- [TPO Roofing Insurance](url): Coverage for thermoplastic polyolefin (TPO) and modified bitumen roofing systems
- [Insurance Score Ratings](url): How ISO insurance scoring affects your premiums
```

### ❌ No "Optional" Section

```markdown
## All Pages

- [Essential Page](url)
- [Blog Post from 2019](url)
- [Important Service](url)
- [Old Press Release](url)
```

**✅ Better:**

```markdown
## Key Services

- [Essential Page](url): Core offering
- [Important Service](url): Main service

## Optional

- [Blog Archive](url): Historical posts
- [Press Releases](url): Media coverage
```

### ❌ Relative URLs

```markdown
- [About](/about)
- [Services](/services)
```

**✅ Better:**

```markdown
- [About](https://yourdomain.com/about): Company information
- [Services](https://yourdomain.com/services): What we offer
```

---

## Advanced Techniques

### Dynamic llms.txt Generation

**For sites with frequently changing content:**

```python
# generate_llms_txt.py
from datetime import datetime

def generate_llms_txt(products, blog_posts):
    output = f"""# {SITE_NAME}

> {SITE_DESCRIPTION}

{SITE_DETAILS}

## Products

"""
    for product in products[:10]:  # Top 10 products
        output += f"- [{product.name}]({product.url}): {product.description}\n"

    output += "\n## Recent Content\n\n"
    for post in blog_posts[:5]:  # Latest 5 posts
        output += f"- [{post.title}]({post.url}): {post.excerpt}\n"

    output += "\n## Optional\n\n"
    output += f"- [All Products]({SITE_URL}/products): Complete catalog\n"
    output += f"- [Blog Archive]({SITE_URL}/blog): All posts\n"

    return output

# Save to file
with open('/path/to/webroot/llms.txt', 'w') as f:
    f.write(generate_llms_txt(products, blog_posts))
```

### Multi-Language Support

**For international sites:**

```markdown
# Company Name

> English summary of your business.

## English Resources

- [English Docs](url): Documentation in English
- [English Support](url): Customer service

## Spanish / Español

- [Documentación en Español](url): Spanish documentation
- [Soporte en Español](url): Servicio al cliente

## French / Français

- [Documentation en Français](url): Documentation française
- [Support en Français](url): Service client
```

### API Documentation Pattern

**For developer-focused sites:**

```markdown
# API Name

> Description of what your API does.

## Getting Started

- [Quick Start Guide](url): Create your first request in 5 minutes
- [Authentication](url): API keys and OAuth setup
- [Rate Limits](url): Request quotas and best practices

## API Reference

- [Endpoints](url): Complete endpoint documentation
- [Request Format](url): JSON schema and examples
- [Response Codes](url): HTTP status codes and error handling

## SDKs

- [Python SDK](url): pip install your-api
- [JavaScript SDK](url): npm install your-api
- [Ruby SDK](url): gem install your-api

## Optional

- [Changelog](url): API version history
- [Migration Guides](url): Upgrading between versions
```

---

## Resources and Tools

### Official Resources

- **Specification**: https://llmstxt.org/
- **GitHub**: https://github.com/answerdotai/llms-txt
- **Domain Examples**: https://llmstxt.org/domains.html
- **Community Directory**: https://llmstxt.site/

### Tools and Libraries

**Python:**
- `llms-txt` - CLI tool and Python module
- `pip install llms-txt`

**JavaScript/Node:**
- vitepress-plugin-llms: https://github.com/okineadev/vitepress-plugin-llms
- docusaurus-plugin-llms: https://github.com/rachfop/docusaurus-plugin-llms

**PHP:**
- llms-txt-php: https://github.com/raphaelstolt/llms-txt-php

**CMS Plugins:**
- Drupal LLM Support: https://www.drupal.org/project/llm_support

### Community

- **Discord**: https://discord.gg/aJPygMvPEN
- **Discussions**: https://github.com/AnswerDotAI/llms-txt/discussions

---

## Quick Reference

### Minimal llms.txt Template

```markdown
# Your Site Name

> One sentence describing what you do.

Brief paragraph with key details about your site, services, or project.

## Main Section

- [Important Page](https://yourdomain.com/page): What this page contains
- [Another Key Page](https://yourdomain.com/page2): Description

## Optional

- [Extra Resources](https://yourdomain.com/extra): Secondary content
```

### Validation Checklist

- [ ] File at `/llms.txt` in website root
- [ ] UTF-8 plain text encoding
- [ ] H1 header with site name
- [ ] Blockquote with summary (recommended)
- [ ] All links absolute URLs with https://
- [ ] Link descriptions are clear and informative
- [ ] "Optional" section separates secondary content
- [ ] No unexplained acronyms or jargon
- [ ] Tested with at least one LLM
- [ ] Key pages have `.md` versions
- [ ] Server configured to serve .md files

---

## When to Use This Skill

**Activate llms-txt-writer skill when:**
- Creating new websites or web properties
- Optimizing sites for AI search engines
- Adding llms.txt files to existing domains
- Reviewing or improving current llms.txt implementations
- Preparing documentation for LLM consumption
- Building AI-friendly knowledge bases
- Enhancing website discoverability for AI agents

**This skill provides:**
- Complete format specifications
- Industry-specific templates
- Best practices and common mistakes
- Testing and validation strategies
- Implementation guides
- SEO optimization techniques
- Real-world examples

---

## Output Guidelines

When helping users create llms.txt files:

1. **Ask clarifying questions:**
   - What industry/niche is this site?
   - What are the 3-5 most important pages?
   - Who is the target audience?
   - What actions do you want visitors to take?

2. **Provide customized template:**
   - Use appropriate industry template
   - Include relevant keywords naturally
   - Organize sections logically
   - Add clear, informative descriptions

3. **Explain the structure:**
   - Why each section is included
   - How LLMs will interpret it
   - What makes descriptions effective

4. **Recommend markdown pages:**
   - Identify key pages needing .md versions
   - Suggest conversion methods
   - Explain server configuration

5. **Validate and test:**
   - Review for common mistakes
   - Suggest testing approaches
   - Provide improvement recommendations

---

**Remember:** The goal is to help large language models understand your website quickly and accurately. Every element should serve that purpose.

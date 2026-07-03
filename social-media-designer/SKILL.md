---
name: social-media-designer
description: "Generate branded social-media ad images (Facebook/Instagram) with Gemini image generation — logo-referenced, percentage-based layout prompts, brand colors; adapt logo/brand paths per client. TRIGGER: create a social media post image, FB/IG ad graphic, branded promo image. DO NOT TRIGGER for posting/scheduling to platforms or writing captions — image generation only."
---

# Social Media Designer Skill

## Purpose
Generate professional, branded social media advertisement images for Contractor's Choice Agency and other Josh websites using Gemini 3 Pro Image Generation.

## Activation Triggers
- "create social media post"
- "make a Facebook post image"
- "generate Instagram ad"
- "social media image for [topic]"
- "branded post for CCA"
- Working with posts in JOSH-SOCIAL-APPROVE project

## Key Learnings (What Works)

### 1. Logo Reference is Critical
Always include the brand logo as a reference image:
```
reference_image_paths: ["/home/josh/gemini_images/CCA-LOGO.jpeg"]
```

### 2. Structured Layout Prompt Format
Use percentage-based sections:
```
TOP HEADER BAR (10%):
- Logo placement, website URL

CENTER CONTENT (70%):
- Hero statistic/text
- Supporting content

FOOTER/CTA (20%):
- Call to action button
- Phone number, contact info
```

### 3. Specific Color Codes
Always provide exact hex codes:
- Navy blue: #1a2744
- Accent red: #dc3545
- White: pure white
- Gray text: neutral gray

### 4. Typography Direction
Be specific about:
- Font weight (ultra-bold, heavy)
- Size relationships (massive, large, small)
- Positioning (centered, left-aligned)

### 5. Visual Elements
Describe specific graphic elements:
- "REJECTED stamp tilted 15 degrees"
- "Subtle texture overlay"
- "Red CTA button with arrow"

## Brand Assets

### Contractor's Choice Agency
- **Logo:** `/home/josh/gemini_images/CCA-LOGO.jpeg`
- **Website:** contractorschoiceagency.com
- **Phone:** 844-967-5247
- **Colors:** Navy (#1a2744), Red (#dc3545), White, Gray

## Prompt Template

```
Create a professional social media advertisement post. Use the exact logo from the reference image in the top-left corner of the design.

DESIGN SPECIFICATIONS:

TOP HEADER BAR (10%):
- Navy blue bar with the exact [BRAND] logo from the reference
- Right side: "[WEBSITE]" in white

CENTER CONTENT (70%):
Background: Deep navy blue (#1a2744) with subtle texture
- Massive white "[MAIN STATISTIC]" taking up significant space - this is the hero element
- [VISUAL ELEMENT if applicable]
- White text: "[MAIN MESSAGE]"
- Gray subtext: "[SUPPORTING DETAIL]"
- Red accent text: "[URGENCY/WARNING TEXT]"

FOOTER/CTA (20%):
- Bright red CTA button: "[CTA TEXT] →"
- White phone icon + "[PHONE NUMBER]"
- Small "FREE QUOTE" badge

STYLE: High-end insurance marketing. Bold, clean, professional. The design should stop someone scrolling. Modern corporate aesthetic like top insurance company ads. 1:1 square format for social media.
```

## Post Categories & Visual Themes

### Statistics/Data Posts
- Giant percentage or number as hero
- Stamp overlays (REJECTED, WARNING, ALERT)
- Clean data visualization feel

### Warning/Trap Posts
- Red accent elements
- Caution/alert iconography
- Urgent typography

### State-Specific Posts
- Geographic elements
- State-related imagery
- Compliance/regulation feel

### Educational/Guide Posts
- Clean, organized layout
- Checklist or step imagery
- Professional, trustworthy aesthetic

## Generation Settings

```json
{
  "aspect_ratio": "1:1",
  "image_size": "2K",
  "output_format": "png",
  "enhance_prompt": true,
  "reference_image_paths": ["[LOGO_PATH]"]
}
```

## Output Location
Save to: `/home/josh/Josh-AI/websites/JOSH-SOCIAL-APPROVE/POSTS/`

Naming convention: `[topic-slug]-social-v[version].png`

## Usage Example

```
User: Create a social media post for "The Additional Insured Trap"

1. Look up post content from database/seed file
2. Apply template with:
   - Main stat or hook from content
   - Supporting text
   - CTA from post
3. Generate with logo reference
4. Save to POSTS folder
```

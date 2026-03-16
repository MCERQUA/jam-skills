# Image Strategy

Every section needs real images. Never deliver a site with broken image paths or placeholder URLs.

---

## Image Sources (in priority order)

### 1. Client-Provided Images
Best case. Ask during brand intake: "Do you have photos we can use — team photos, office, product shots, work examples?"

If they provide images:
- Save to `public/images/` in the project
- Convert to WebP for smaller file size: `ffmpeg -i input.jpg -q:v 80 output.webp`
- Resize to max 1920px wide for heroes, 800px for cards
- Always keep originals in a `public/images/originals/` folder

### 2. AI-Generated Images (Gemini)
Use the gemini-image skill for custom images that match the brand:

```
Read /mnt/shared-skills/gemini-image/SKILL.md
```

Good for:
- Hero background images (abstract, branded)
- Service illustrations
- Blog post featured images
- Pattern/texture backgrounds
- Icon illustrations

**Prompt pattern for website images:**
```
Professional [industry] photograph, [description], modern clean aesthetic,
[brand color] accent lighting, dark moody background, high quality,
photorealistic, 16:9 aspect ratio
```

**Save immediately** to `public/images/` — never keep generated images only in memory.

### 3. Stock Photos (Unsplash)
For generic professional photos when AI generation isn't ideal (real people, specific locations):

```tsx
// next.config.ts — add Unsplash domain
images: {
  remotePatterns: [
    { protocol: "https", hostname: "images.unsplash.com" },
  ],
}
```

Search Unsplash topics:
- Business/office: `https://unsplash.com/s/photos/office-modern`
- Construction/trades: `https://unsplash.com/s/photos/construction`
- Technology: `https://unsplash.com/s/photos/technology`
- Team/people: `https://unsplash.com/s/photos/team-meeting`

**Download and save locally** — don't hot-link from Unsplash in production. Save to `public/images/`.

### 4. Icon Illustrations (Lucide + Custom SVG)
For feature icons, service icons, process step icons:

```tsx
import { Shield, Zap, Heart } from "lucide-react";

// Consistent sizing
<Shield className="w-6 h-6 text-primary" />
```

For custom icons, use the icon-generation skill:
```
Read /mnt/shared-skills/icon-generation/SKILL.md
```

---

## Required Images per Page

### Home Page
| Image | Size | Source |
|-------|------|--------|
| Hero background or illustration | 1920x1080 | AI-generated or client photo |
| Feature icons (6) | SVG | Lucide React |
| Testimonial avatars (3) | 64x64 | Client-provided or AI-generated |
| Client/partner logos (if marquee) | SVG or 200x80 | Client-provided |

### About Page
| Image | Size | Source |
|-------|------|--------|
| Hero image (office/team/product) | 800x600 | Client photo preferred |
| Team member photos (3-6) | 256x256 | Client-provided (crop to square) |
| Story/history image | 800x500 | Client photo or stock |

### Services Page
| Image | Size | Source |
|-------|------|--------|
| Service icons (3-6) | SVG | Lucide React |
| Process step icons | SVG | Lucide React or numbered |

### Blog Posts
| Image | Size | Source |
|-------|------|--------|
| Featured image per post | 1200x630 | AI-generated or stock |
| In-post images | 800x auto | Varies |

### Global
| Image | Size | Source |
|-------|------|--------|
| Logo | SVG preferred | Client-provided |
| Favicon | 32x32 + 180x180 | Derived from logo |
| OG image (default) | 1200x630 | AI-generated with logo + tagline |

---

## OG Image Generation

Create a default OG image for social sharing. Save to `public/og/default.png`.

**Option 1: AI-generated** — Use gemini-image with prompt:
```
Professional social media card, dark background [brand color] accents,
"[Business Name]" text centered, "[Tagline]" below, clean modern design,
1200x630 pixels, no bleed, contained within frame
```

**Option 2: Next.js OG Image Generation** — Dynamic OG images per page:
```tsx
// src/app/og/route.tsx
import { ImageResponse } from "next/og";

export async function GET() {
  return new ImageResponse(
    (
      <div style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #0a0a0a, #1a1a2e)",
        color: "#e2e8f0",
        fontFamily: "system-ui",
      }}>
        <div style={{ fontSize: 60, fontWeight: 700 }}>Business Name</div>
        <div style={{ fontSize: 24, color: "#94a3b8", marginTop: 16 }}>
          Your tagline here
        </div>
      </div>
    ),
    { width: 1200, height: 630 }
  );
}
```

---

## Favicon Generation

From the client's logo, create:
1. `public/favicon.ico` — 32x32 (ICO format)
2. `public/apple-touch-icon.png` — 180x180
3. `public/icon.svg` — SVG version (if logo is SVG)

Add to `src/app/layout.tsx`:
```tsx
export const metadata: Metadata = {
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
};
```

If client has no logo yet, generate a simple monogram:
- First letter of business name
- Brand primary color background
- White text
- Save as both ICO and PNG

---

## Image Optimization Checklist

Before delivery:
- [ ] All images in WebP format (except SVG icons)
- [ ] Hero images: max 1920px wide, < 200KB
- [ ] Card images: max 800px wide, < 100KB
- [ ] All `<Image>` components have `width`, `height`, and `alt`
- [ ] Hero image has `priority` prop
- [ ] Below-fold images use default lazy loading
- [ ] No broken image paths (test every page)
- [ ] OG image exists at `/og/default.png`
- [ ] Favicon exists at `/favicon.ico`

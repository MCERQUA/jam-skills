# SEO Setup

Every website MUST have these configured before delivery.

---

## Metadata (layout.tsx)

```tsx
export const metadata: Metadata = {
  metadataBase: new URL("https://www.example.com"),
  title: {
    default: "Business Name — What They Do",
    template: "%s | Business Name",
  },
  description: "Compelling 150-160 char description with primary keyword.",
  keywords: ["keyword1", "keyword2", "keyword3"],
  authors: [{ name: "Business Name" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://www.example.com",
    siteName: "Business Name",
    title: "Business Name — What They Do",
    description: "Same or similar to meta description.",
    images: [
      {
        url: "/og/default.png",
        width: 1200,
        height: 630,
        alt: "Business Name",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Business Name — What They Do",
    description: "Same or similar to meta description.",
    images: ["/og/default.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
};
```

### Per-page metadata:
Each page should override title and description:
```tsx
// src/app/about/page.tsx
export const metadata: Metadata = {
  title: "About Us",  // Becomes "About Us | Business Name" via template
  description: "Page-specific description with relevant keywords.",
};
```

---

## Sitemap (src/app/sitemap.ts)

```tsx
import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://www.example.com";

  return [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "monthly", priority: 1 },
    { url: `${baseUrl}/about`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.8 },
    { url: `${baseUrl}/services`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.9 },
    { url: `${baseUrl}/contact`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
    { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.8 },
  ];
}
```

---

## Robots (src/app/robots.ts)

```tsx
import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/admin/"],
    },
    sitemap: "https://www.example.com/sitemap.xml",
  };
}
```

---

## Structured Data (JSON-LD)

Add to the root layout or specific pages:

### Local Business:
```tsx
<script
  type="application/ld+json"
  dangerouslySetInnerHTML={{
    __html: JSON.stringify({
      "@context": "https://schema.org",
      "@type": "LocalBusiness",
      name: "Business Name",
      description: "What the business does.",
      url: "https://www.example.com",
      telephone: "+1-555-000-0000",
      address: {
        "@type": "PostalAddress",
        streetAddress: "123 Main St",
        addressLocality: "City",
        addressRegion: "ST",
        postalCode: "00000",
        addressCountry: "US",
      },
      openingHoursSpecification: [
        {
          "@type": "OpeningHoursSpecification",
          dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
          opens: "08:00",
          closes: "17:00",
        },
      ],
    }),
  }}
/>
```

### Professional Service:
Use `@type: "ProfessionalService"` with the same pattern.

### Blog Article:
```tsx
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "author": { "@type": "Person", "name": "Author Name" },
  "datePublished": "2026-01-01",
  "publisher": {
    "@type": "Organization",
    "name": "Business Name",
    "logo": { "@type": "ImageObject", "url": "https://example.com/logo.png" }
  }
}
```

---

## Image SEO

- Every `<Image>` must have a descriptive `alt` attribute
- Use descriptive filenames (`team-photo-office.jpg` not `IMG_0042.jpg`)
- Provide `width` and `height` to prevent layout shift
- Use `priority` on above-the-fold hero images
- Use `loading="lazy"` (default) for below-fold images

---

## Heading Hierarchy

Every page MUST have exactly one `<h1>` (usually in the hero section). Use descending order:
- `<h1>` — Main page heading (one per page)
- `<h2>` — Section headings
- `<h3>` — Sub-section headings
- Never skip levels (no h1 → h3)

---

## Reference

For deeper SEO guidance specific to local/service businesses:
```
Read /mnt/shared-skills/marketing/local-seo/SKILL.md
```

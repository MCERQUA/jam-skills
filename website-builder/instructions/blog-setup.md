# Blog Setup with MDX

Full blog system: MDX content files, dynamic routing, post metadata, categories, RSS feed.

---

## Directory Structure

```
src/
├── app/
│   └── blog/
│       ├── page.tsx              ← Blog index (lists all posts)
│       └── [slug]/
│           └── page.tsx          ← Individual post (dynamic route)
├── lib/
│   └── blog.ts                  ← Post loading utilities
└── content/
    └── posts/
        ├── getting-started.mdx   ← Blog posts as MDX files
        ├── industry-trends.mdx
        └── success-story.mdx
```

---

## Step 1: Install MDX Dependencies

```bash
pnpm add @next/mdx @mdx-js/loader @mdx-js/react gray-matter reading-time
```

---

## Step 2: Blog Post Format

Each `.mdx` file in `src/content/posts/`:

```mdx
---
title: "How to Get Started with Our Services"
description: "A comprehensive guide to making the most of what we offer."
date: "2026-03-15"
category: "Guide"
image: "/images/blog/getting-started.webp"
author: "Team Name"
---

Your blog content goes here. MDX supports all Markdown syntax plus JSX components.

## Subheading

Regular paragraphs, **bold text**, *italic text*, [links](https://example.com).

- Bullet lists
- Work just fine

### Code blocks too

```javascript
const example = "hello world";
```

> Blockquotes for emphasis or callouts.
```

---

## Step 3: Post Loading Utility

```tsx
// src/lib/blog.ts
import fs from "fs";
import path from "path";
import matter from "gray-matter";
import readingTime from "reading-time";

const postsDirectory = path.join(process.cwd(), "src/content/posts");

export interface Post {
  slug: string;
  title: string;
  description: string;
  date: string;
  category: string;
  image: string;
  author: string;
  readTime: string;
  content: string;
}

export function getAllPosts(): Post[] {
  if (!fs.existsSync(postsDirectory)) return [];

  const files = fs.readdirSync(postsDirectory).filter((f) => f.endsWith(".mdx"));

  const posts = files.map((filename) => {
    const slug = filename.replace(/\.mdx$/, "");
    const filePath = path.join(postsDirectory, filename);
    const fileContent = fs.readFileSync(filePath, "utf8");
    const { data, content } = matter(fileContent);

    return {
      slug,
      title: data.title || slug,
      description: data.description || "",
      date: data.date || "",
      category: data.category || "General",
      image: data.image || "",
      author: data.author || "",
      readTime: readingTime(content).text,
      content,
    };
  });

  // Sort by date descending
  return posts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

export function getPostBySlug(slug: string): Post | null {
  const filePath = path.join(postsDirectory, `${slug}.mdx`);
  if (!fs.existsSync(filePath)) return null;

  const fileContent = fs.readFileSync(filePath, "utf8");
  const { data, content } = matter(fileContent);

  return {
    slug,
    title: data.title || slug,
    description: data.description || "",
    date: data.date || "",
    category: data.category || "General",
    image: data.image || "",
    author: data.author || "",
    readTime: readingTime(content).text,
    content,
  };
}

export function getAllCategories(): string[] {
  const posts = getAllPosts();
  return [...new Set(posts.map((p) => p.category))];
}
```

---

## Step 4: Blog Index Page

```tsx
// src/app/blog/page.tsx
import type { Metadata } from "next";
import { getAllPosts } from "@/lib/blog";
import { Navbar } from "@/components/sections/Navbar";
import { Footer } from "@/components/sections/Footer";
import { FadeIn } from "@/components/animations/FadeIn";
import { StaggerChildren, StaggerItem } from "@/components/animations/StaggerChildren";
import Image from "next/image";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Blog",
  description: "Insights, tips, and industry news.",
};

export default function BlogPage() {
  const posts = getAllPosts();

  return (
    <main>
      <Navbar />

      <section className="pt-32 pb-12 md:pt-40">
        <div className="max-w-4xl mx-auto px-4 md:px-6 text-center">
          <FadeIn>
            <h1 className="text-4xl md:text-6xl font-heading font-bold">
              Our{" "}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Blog
              </span>
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Insights, guides, and updates from our team.
            </p>
          </FadeIn>
        </div>
      </section>

      <section className="pb-24 md:pb-32">
        <div className="max-w-7xl mx-auto px-4 md:px-6">
          <StaggerChildren className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
            {posts.map((post) => (
              <StaggerItem key={post.slug}>
                <Link href={`/blog/${post.slug}`} className="group block">
                  <article className="rounded-xl overflow-hidden bg-card border border-border group-hover:border-primary/30 transition-colors h-full flex flex-col">
                    {post.image && (
                      <div className="relative aspect-[16/10] overflow-hidden">
                        <Image
                          src={post.image}
                          alt={post.title}
                          fill
                          className="object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute top-3 left-3 px-2.5 py-1 bg-primary/90 text-primary-foreground text-xs font-semibold rounded-md">
                          {post.category}
                        </div>
                      </div>
                    )}
                    <div className="p-6 flex-grow flex flex-col">
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                        <span>{new Date(post.date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</span>
                        <span>&middot;</span>
                        <span>{post.readTime}</span>
                      </div>
                      <h2 className="text-lg font-heading font-semibold group-hover:text-primary transition-colors line-clamp-2">
                        {post.title}
                      </h2>
                      <p className="mt-2 text-sm text-muted-foreground line-clamp-2 flex-grow">
                        {post.description}
                      </p>
                    </div>
                  </article>
                </Link>
              </StaggerItem>
            ))}
          </StaggerChildren>
        </div>
      </section>

      <Footer />
    </main>
  );
}
```

---

## Step 5: Individual Post Page

```tsx
// src/app/blog/[slug]/page.tsx
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getAllPosts, getPostBySlug } from "@/lib/blog";
import { Navbar } from "@/components/sections/Navbar";
import { Footer } from "@/components/sections/Footer";
import { CTA } from "@/components/sections/CTA";
import { FadeIn } from "@/components/animations/FadeIn";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

// Generate static paths at build time
export function generateStaticParams() {
  const posts = getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}

// Dynamic metadata per post
export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const post = getPostBySlug(params.slug);
  if (!post) return {};

  return {
    title: post.title,
    description: post.description,
    openGraph: {
      title: post.title,
      description: post.description,
      type: "article",
      publishedTime: post.date,
      images: post.image ? [{ url: post.image }] : [],
    },
  };
}

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = getPostBySlug(params.slug);
  if (!post) notFound();

  return (
    <main>
      <Navbar />

      <article className="pt-32 pb-16 md:pt-40">
        <div className="max-w-3xl mx-auto px-4 md:px-6">
          <FadeIn>
            {/* Back link */}
            <Link
              href="/blog"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to blog
            </Link>

            {/* Post header */}
            <div className="mb-8">
              <div className="flex items-center gap-3 text-sm text-muted-foreground mb-4">
                <span className="px-2.5 py-0.5 bg-primary/10 text-primary rounded-md text-xs font-semibold">
                  {post.category}
                </span>
                <span>{new Date(post.date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</span>
                <span>&middot;</span>
                <span>{post.readTime}</span>
              </div>
              <h1 className="text-3xl md:text-5xl font-heading font-bold leading-tight">
                {post.title}
              </h1>
              {post.author && (
                <p className="mt-4 text-muted-foreground">By {post.author}</p>
              )}
            </div>

            {/* Featured image */}
            {post.image && (
              <div className="relative aspect-[16/9] rounded-xl overflow-hidden mb-10">
                <Image
                  src={post.image}
                  alt={post.title}
                  fill
                  className="object-cover"
                  priority
                />
              </div>
            )}

            {/* Post content — rendered as HTML from MDX */}
            <div className="prose prose-invert prose-lg max-w-none
              prose-headings:font-heading prose-headings:font-bold
              prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
              prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
              prose-p:text-muted-foreground prose-p:leading-relaxed
              prose-a:text-primary prose-a:no-underline hover:prose-a:underline
              prose-strong:text-foreground
              prose-blockquote:border-primary/50 prose-blockquote:text-muted-foreground
              prose-code:text-primary prose-code:bg-card prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
              prose-pre:bg-card prose-pre:border prose-pre:border-border
              prose-img:rounded-xl
              prose-li:text-muted-foreground
            ">
              {/* TODO: Render MDX content here. Options:
                  1. Use @next/mdx with MDXRemote
                  2. Use a markdown renderer like react-markdown
                  3. Pre-compile MDX at build time */}
              <div dangerouslySetInnerHTML={{ __html: "<!-- MDX content renders here -->" }} />
            </div>
          </FadeIn>
        </div>
      </article>

      <CTA />
      <Footer />
    </main>
  );
}
```

---

## Step 6: Add to Sitemap

Update `src/app/sitemap.ts` to include blog posts:

```tsx
import { MetadataRoute } from "next";
import { getAllPosts } from "@/lib/blog";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://www.example.com";
  const posts = getAllPosts();

  const blogUrls = posts.map((post) => ({
    url: `${baseUrl}/blog/${post.slug}`,
    lastModified: new Date(post.date),
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  return [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "monthly", priority: 1 },
    { url: `${baseUrl}/about`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.8 },
    { url: `${baseUrl}/services`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.9 },
    { url: `${baseUrl}/contact`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
    { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.8 },
    ...blogUrls,
  ];
}
```

---

## Step 7: Starter Blog Posts

Create 2-3 starter posts for the client. Use the copywriting skill for quality:
```
Read /mnt/shared-skills/marketing/copywriting/SKILL.md
```

**Starter post ideas by industry:**
- Service business: "X Things to Look For When Hiring a [Service Provider]"
- Tech/SaaS: "Getting Started Guide: Your First 30 Days"
- E-commerce: "How to Choose the Right [Product] for Your Needs"
- Any business: "Meet the Team Behind [Business Name]"

Each post should be 500-800 words minimum with a real featured image.

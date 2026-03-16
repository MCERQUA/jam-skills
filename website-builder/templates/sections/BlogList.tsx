"use client";
import { ArrowRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { FadeIn } from "@/components/animations/FadeIn";
import { StaggerChildren, StaggerItem } from "@/components/animations/StaggerChildren";

interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  image?: string;
  date: string;
  category: string;
  readTime?: string;
}

interface BlogListProps {
  title?: string;
  titleAccent?: string;
  label?: string;
  posts?: BlogPost[];
}

const DEFAULT_POSTS: BlogPost[] = [
  {
    slug: "getting-started",
    title: "How to Get Started with Our Services",
    excerpt: "A comprehensive guide to making the most of what we offer from day one.",
    image: "/images/blog/post-1.webp",
    date: "March 15, 2026",
    category: "Guide",
    readTime: "5 min read",
  },
  {
    slug: "industry-trends",
    title: "Top Industry Trends to Watch in 2026",
    excerpt: "Stay ahead of the curve with our analysis of the biggest changes happening this year.",
    image: "/images/blog/post-2.webp",
    date: "March 10, 2026",
    category: "Industry",
    readTime: "8 min read",
  },
  {
    slug: "success-story",
    title: "How We Helped XYZ Company Grow 300%",
    excerpt: "A deep dive into the strategy and execution that drove exceptional results.",
    image: "/images/blog/post-3.webp",
    date: "March 5, 2026",
    category: "Case Study",
    readTime: "6 min read",
  },
];

const DEFAULTS = {
  label: "Blog",
  title: "Latest ",
  titleAccent: "Insights",
};

export function BlogList(props: BlogListProps) {
  const label = props.label ?? DEFAULTS.label;
  const title = props.title ?? DEFAULTS.title;
  const titleAccent = props.titleAccent ?? DEFAULTS.titleAccent;
  const posts = props.posts ?? DEFAULT_POSTS;

  return (
    <section className="py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        <FadeIn className="flex items-end justify-between mb-12">
          <div>
            <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
              {label}
            </p>
            <h2 className="text-3xl md:text-5xl font-heading font-bold">
              {title}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                {titleAccent}
              </span>
            </h2>
          </div>
          <Link
            href="/blog"
            className="hidden md:flex items-center gap-1 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
          >
            View all posts
            <ArrowRight className="w-4 h-4" />
          </Link>
        </FadeIn>

        <StaggerChildren className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {posts.map((post) => (
            <StaggerItem key={post.slug}>
              <Link href={`/blog/${post.slug}`} className="group block">
                <article className="rounded-xl overflow-hidden bg-card border border-border group-hover:border-primary/30 transition-colors">
                  {/* Image */}
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

                  {/* Content */}
                  <div className="p-6">
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                      <span>{post.date}</span>
                      {post.readTime && (
                        <>
                          <span>&middot;</span>
                          <span>{post.readTime}</span>
                        </>
                      )}
                    </div>
                    <h3 className="text-lg font-heading font-semibold group-hover:text-primary transition-colors line-clamp-2">
                      {post.title}
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                      {post.excerpt}
                    </p>
                  </div>
                </article>
              </Link>
            </StaggerItem>
          ))}
        </StaggerChildren>

        {/* Mobile "View all" link */}
        <div className="mt-8 text-center md:hidden">
          <Link
            href="/blog"
            className="inline-flex items-center gap-1 text-sm font-medium text-primary"
          >
            View all posts
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}

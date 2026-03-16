// Blog Page Composition Template
//
// All section components accept optional props for customization.

import type { Metadata } from "next";
import { Navbar } from "@/components/sections/Navbar";
import { BlogList } from "@/components/sections/BlogList";
import { CTA } from "@/components/sections/CTA";
import { Footer } from "@/components/sections/Footer";
import { FadeIn } from "@/components/animations/FadeIn";

export const metadata: Metadata = {
  title: "Blog",
  description: "Insights, tips, and industry news to help you stay informed.",
};

export default function BlogPage() {
  return (
    <main>
      <Navbar
        logo="Acme Co"
        cta={{ label: "Get a Quote", href: "/contact" }}
      />

      {/* Blog Hero */}
      <section className="pt-32 pb-12 md:pt-40 md:pb-16">
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

      {/* Blog List */}
      <BlogList
        posts={[
          {
            slug: "getting-started",
            title: "How to Get Started with Our Services",
            excerpt: "A comprehensive guide to making the most of what we offer.",
            image: "/images/blog/post-1.webp",
            date: "March 15, 2026",
            category: "Guide",
            readTime: "5 min read",
          },
          {
            slug: "industry-trends",
            title: "Top Industry Trends to Watch in 2026",
            excerpt: "Stay ahead with our analysis of the biggest changes this year.",
            image: "/images/blog/post-2.webp",
            date: "March 10, 2026",
            category: "Industry",
            readTime: "8 min read",
          },
          {
            slug: "success-story",
            title: "How We Helped XYZ Company Grow 300%",
            excerpt: "A deep dive into the strategy that drove exceptional results.",
            image: "/images/blog/post-3.webp",
            date: "March 5, 2026",
            category: "Case Study",
            readTime: "6 min read",
          },
        ]}
      />

      <CTA
        title="Have a Question?"
        description="Reach out and we'll get back to you within 24 hours."
        primaryCTA="Contact Us"
        primaryHref="/contact"
        phone="(555) 000-0000"
      />

      <Footer
        businessName="Acme Co"
        phone="(555) 000-0000"
        email="hello@example.com"
        address="123 Main Street, City, ST 00000"
      />
    </main>
  );
}

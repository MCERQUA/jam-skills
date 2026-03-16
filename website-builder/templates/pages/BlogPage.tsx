// Blog Page Composition Template

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
      <Navbar />

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
      <BlogList />

      <CTA />
      <Footer />
    </main>
  );
}

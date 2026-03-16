// Home Page Composition Template
// Copy sections from templates/sections/ into src/components/sections/
// Then compose this page from them.
//
// All section components accept optional props for customization.
// Without props, they render with sensible defaults.

import { Navbar } from "@/components/sections/Navbar";
import { Hero } from "@/components/sections/Hero";
import { Features } from "@/components/sections/Features";
import { Stats } from "@/components/sections/Stats";
import { Testimonials } from "@/components/sections/Testimonials";
import { CTA } from "@/components/sections/CTA";
import { Footer } from "@/components/sections/Footer";

// Optional additions:
// import { InfiniteMarquee } from "@/components/animations/InfiniteMarquee";
// import { BlogList } from "@/components/sections/BlogList";
// import { Pricing } from "@/components/sections/Pricing";

export default function HomePage() {
  return (
    <main>
      <Navbar
        logo="Acme Co"
        navItems={[
          { label: "Home", href: "/" },
          { label: "About", href: "/about" },
          { label: "Services", href: "/services" },
          { label: "Blog", href: "/blog" },
          { label: "Contact", href: "/contact" },
        ]}
        cta={{ label: "Get a Quote", href: "/contact" }}
      />

      <Hero
        title="Your Headline That"
        titleAccent=" Communicates Value"
        subtitle="A clear, benefit-focused description that tells visitors exactly what you do and why they should care."
        badge="Now accepting new clients"
        primaryCTA="Get a Free Quote"
        primaryHref="/contact"
        secondaryCTA="View Our Services"
        secondaryHref="/services"
      />

      {/* Optional: Logo marquee between Hero and Features */}
      {/* <InfiniteMarquee speed={25}>
        <div className="flex items-center gap-16 px-8 py-6">
          client logos here
        </div>
      </InfiniteMarquee> */}

      <Features
        label="Why Choose Us"
        title="Everything You Need, "
        titleAccent="Nothing You Don't"
        subtitle="We focus on what matters most to deliver real results for your business."
        features={[
          { icon: "shield", title: "Reliable Service", description: "Consistent quality you can count on." },
          { icon: "zap", title: "Fast Response", description: "Quick turnaround times." },
          { icon: "heart", title: "Customer First", description: "Every decision starts with you." },
          { icon: "clock", title: "Available 24/7", description: "Round-the-clock support." },
          { icon: "award", title: "Industry Experts", description: "Years of experience." },
          { icon: "users", title: "Trusted Team", description: "Vetted professionals." },
        ]}
      />

      <Stats
        stats={[
          { value: 500, suffix: "+", label: "Happy Clients" },
          { value: 15, suffix: "+", label: "Years Experience" },
          { value: 98, suffix: "%", label: "Satisfaction Rate" },
          { value: 24, suffix: "/7", label: "Support Available" },
        ]}
      />

      <Testimonials
        testimonials={[
          { name: "Sarah Johnson", role: "Homeowner", text: "Outstanding service. Highly recommend.", rating: 5 },
          { name: "Mike Chen", role: "Business Owner", text: "Professional, punctual, and fair pricing.", rating: 5 },
          { name: "Lisa Rodriguez", role: "Property Manager", text: "Fast response and excellent communication.", rating: 5 },
        ]}
      />

      {/* Optional: <Pricing /> */}
      {/* Optional: <BlogList /> */}

      <CTA
        title="Ready to Get Started?"
        description="Contact us today for a free consultation."
        primaryCTA="Get Your Free Quote"
        primaryHref="/contact"
        phone="(555) 000-0000"
      />

      <Footer
        businessName="Acme Co"
        description="A short description of the business and what makes it special."
        phone="(555) 000-0000"
        email="hello@example.com"
        address="123 Main Street, City, ST 00000"
        links={[
          {
            title: "Company",
            items: [
              { label: "About", href: "/about" },
              { label: "Services", href: "/services" },
              { label: "Blog", href: "/blog" },
              { label: "Contact", href: "/contact" },
            ],
          },
          {
            title: "Services",
            items: [
              { label: "Service One", href: "/services#one" },
              { label: "Service Two", href: "/services#two" },
            ],
          },
          {
            title: "Legal",
            items: [
              { label: "Privacy Policy", href: "/privacy" },
              { label: "Terms of Service", href: "/terms" },
            ],
          },
        ]}
      />
    </main>
  );
}

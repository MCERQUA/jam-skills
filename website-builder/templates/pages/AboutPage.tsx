// About Page Composition Template
//
// All section components accept optional props for customization.
// Inline sections (Our Story, Values) use local data — customize directly.

import type { Metadata } from "next";
import { Navbar } from "@/components/sections/Navbar";
import { HeroSplit } from "@/components/sections/HeroSplit";
import { Stats } from "@/components/sections/Stats";
import { CTA } from "@/components/sections/CTA";
import { Footer } from "@/components/sections/Footer";
import { FadeIn } from "@/components/animations/FadeIn";
import { StaggerChildren, StaggerItem } from "@/components/animations/StaggerChildren";

export const metadata: Metadata = {
  title: "About Us",
  description: "Learn about our story, mission, and the team behind the work.",
};

const values = [
  { title: "Quality First", description: "We never cut corners. Every project gets our full attention and expertise." },
  { title: "Transparency", description: "Honest pricing, clear communication, no surprises." },
  { title: "Customer Focus", description: "Your satisfaction drives every decision we make." },
  { title: "Innovation", description: "We stay current with the latest techniques and best practices." },
];

const team = [
  { name: "John Smith", role: "Founder & CEO", image: "/images/team/john.webp" },
  { name: "Jane Doe", role: "Operations Manager", image: "/images/team/jane.webp" },
  { name: "Bob Wilson", role: "Lead Technician", image: "/images/team/bob.webp" },
];

export default function AboutPage() {
  return (
    <main>
      <Navbar
        logo="Acme Co"
        cta={{ label: "Get a Quote", href: "/contact" }}
      />

      {/* Hero — use HeroSplit with about-specific content */}
      <HeroSplit
        title="Our Story"
        titleAccent=" & Mission"
        subtitle="Learn about who we are, why we do what we do, and what drives us forward every day."
        badge="About Us"
        primaryCTA="Meet the Team"
        primaryHref="#team"
        secondaryCTA="Our Services"
        secondaryHref="/services"
        image="/images/about-hero.webp"
        imageAlt="Our team at work"
      />

      {/* Our Story */}
      <section className="py-24 md:py-32">
        <div className="max-w-3xl mx-auto px-4 md:px-6">
          <FadeIn>
            <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
              Our Story
            </p>
            <h2 className="text-3xl md:text-4xl font-heading font-bold mb-6">
              How We Got Here
            </h2>
            <div className="space-y-4 text-lg text-muted-foreground leading-relaxed">
              <p>
                Founded in [year], we started with a simple mission: to provide
                the highest quality service in [industry] while treating every
                customer like family.
              </p>
              <p>
                Over the years, we&apos;ve grown from a small operation to a trusted
                name in the community, but our commitment to quality and personal
                service has never changed.
              </p>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Stats */}
      <Stats
        stats={[
          { value: 500, suffix: "+", label: "Happy Clients" },
          { value: 15, suffix: "+", label: "Years Experience" },
          { value: 98, suffix: "%", label: "Satisfaction Rate" },
          { value: 24, suffix: "/7", label: "Support Available" },
        ]}
      />

      {/* Values */}
      <section className="py-24 md:py-32 bg-card/30">
        <div className="max-w-7xl mx-auto px-4 md:px-6">
          <FadeIn className="text-center mb-16">
            <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
              Our Values
            </p>
            <h2 className="text-3xl md:text-5xl font-heading font-bold">
              What We Stand For
            </h2>
          </FadeIn>

          <StaggerChildren className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {values.map((value, i) => (
              <StaggerItem key={i}>
                <div className="p-8 rounded-xl bg-card border border-border">
                  <h3 className="text-xl font-heading font-semibold mb-2">
                    {value.title}
                  </h3>
                  <p className="text-muted-foreground">{value.description}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerChildren>
        </div>
      </section>

      {/* Team — optional, only if client has team photos */}
      {/* <section className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-4 md:px-6">
          <FadeIn className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-heading font-bold">Meet the Team</h2>
          </FadeIn>
          <StaggerChildren className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {team.map((member, i) => (
              <StaggerItem key={i} className="text-center">
                <div className="relative w-32 h-32 mx-auto rounded-full overflow-hidden border-2 border-border mb-4">
                  <Image src={member.image} alt={member.name} fill className="object-cover" />
                </div>
                <h3 className="font-heading font-semibold">{member.name}</h3>
                <p className="text-sm text-muted-foreground">{member.role}</p>
              </StaggerItem>
            ))}
          </StaggerChildren>
        </div>
      </section> */}

      <CTA
        title="Want to Work With Us?"
        description="We'd love to hear about your project. Reach out for a free consultation."
        primaryCTA="Get in Touch"
        primaryHref="/contact"
        phone="(555) 000-0000"
      />

      <Footer
        businessName="Acme Co"
        description="Quality service since [year]."
        phone="(555) 000-0000"
        email="hello@example.com"
        address="123 Main Street, City, ST 00000"
      />
    </main>
  );
}

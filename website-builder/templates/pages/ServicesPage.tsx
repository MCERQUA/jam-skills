// Services Page Composition Template
//
// Inline sections (hero, service cards, process) use local data — customize directly.
// Shared sections (Navbar, CTA, Footer) accept props.

import type { Metadata } from "next";
import { Navbar } from "@/components/sections/Navbar";
import { CTA } from "@/components/sections/CTA";
import { Footer } from "@/components/sections/Footer";
import { FadeIn } from "@/components/animations/FadeIn";
import { StaggerChildren, StaggerItem } from "@/components/animations/StaggerChildren";
import { ArrowRight, CheckCircle } from "lucide-react";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Our Services",
  description: "Explore our range of professional services designed to meet your needs.",
};

const services = [
  {
    title: "Service One",
    description: "A detailed description of this service, what it includes, and the value it delivers.",
    features: ["Benefit one", "Benefit two", "Benefit three", "Benefit four"],
    price: "From $199",
  },
  {
    title: "Service Two",
    description: "A detailed description of this service, what it includes, and the value it delivers.",
    features: ["Benefit one", "Benefit two", "Benefit three", "Benefit four"],
    price: "From $299",
  },
  {
    title: "Service Three",
    description: "A detailed description of this service, what it includes, and the value it delivers.",
    features: ["Benefit one", "Benefit two", "Benefit three", "Benefit four"],
    price: "From $399",
  },
];

const process = [
  { step: "01", title: "Consultation", description: "We discuss your needs and create a plan." },
  { step: "02", title: "Execution", description: "Our team gets to work with precision and care." },
  { step: "03", title: "Review", description: "We walk you through everything before sign-off." },
  { step: "04", title: "Support", description: "Ongoing support to keep things running smooth." },
];

export default function ServicesPage() {
  return (
    <main>
      <Navbar
        logo="Acme Co"
        cta={{ label: "Get a Quote", href: "/contact" }}
      />

      {/* Hero */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-28">
        <div className="max-w-4xl mx-auto px-4 md:px-6 text-center">
          <FadeIn>
            <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-4">
              Our Services
            </p>
            <h1 className="text-4xl md:text-6xl font-heading font-bold">
              What We{" "}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Offer
              </span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
              Professional solutions tailored to your needs. Each service is designed
              to deliver measurable results.
            </p>
          </FadeIn>
        </div>
      </section>

      {/* Service Cards */}
      <section className="pb-24 md:pb-32">
        <div className="max-w-7xl mx-auto px-4 md:px-6">
          <StaggerChildren className="space-y-8">
            {services.map((service, i) => (
              <StaggerItem key={i}>
                <div className="p-8 md:p-10 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="md:col-span-2">
                      <h2 className="text-2xl font-heading font-bold mb-3">
                        {service.title}
                      </h2>
                      <p className="text-muted-foreground leading-relaxed mb-6">
                        {service.description}
                      </p>
                      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {service.features.map((feature, j) => (
                          <li key={j} className="flex items-center gap-2 text-sm">
                            <CheckCircle className="w-4 h-4 text-primary shrink-0" />
                            <span className="text-muted-foreground">{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="flex flex-col items-start md:items-end justify-between">
                      <p className="text-2xl font-heading font-bold text-primary mb-4">
                        {service.price}
                      </p>
                      <Link
                        href="/contact"
                        className="group flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 transition-colors cursor-pointer"
                      >
                        Get a Quote
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                      </Link>
                    </div>
                  </div>
                </div>
              </StaggerItem>
            ))}
          </StaggerChildren>
        </div>
      </section>

      {/* Process */}
      <section className="py-24 md:py-32 bg-card/30">
        <div className="max-w-7xl mx-auto px-4 md:px-6">
          <FadeIn className="text-center mb-16">
            <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
              Our Process
            </p>
            <h2 className="text-3xl md:text-5xl font-heading font-bold">
              How We Work
            </h2>
          </FadeIn>

          <StaggerChildren className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {process.map((step, i) => (
              <StaggerItem key={i}>
                <div className="text-center p-6">
                  <span className="text-5xl font-heading font-bold text-primary/20">
                    {step.step}
                  </span>
                  <h3 className="text-lg font-heading font-semibold mt-2 mb-2">
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </StaggerItem>
            ))}
          </StaggerChildren>
        </div>
      </section>

      <CTA
        title="Ready to Get Started?"
        description="Contact us today for a free consultation and custom quote."
        primaryCTA="Request a Quote"
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

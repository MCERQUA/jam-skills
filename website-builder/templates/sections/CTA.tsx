"use client";
import { ArrowRight } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";
import { MagneticHover } from "@/components/animations/MagneticHover";
import Link from "next/link";

interface CTAProps {
  title?: string;
  description?: string;
  primaryCTA?: string;
  primaryHref?: string;
  phone?: string;
}

// REPLACE: Pass real CTA content via props.
const DEFAULTS = {
  title: "REPLACE: Your CTA Headline Here",
  description:
    "REPLACE: Compelling reason to take action. Include a specific benefit or offer.",
  primaryCTA: "REPLACE: Action Text",
  primaryHref: "/contact",
  phone: "(555) 000-0000",
};

export function CTA(props: CTAProps) {
  const title = props.title ?? DEFAULTS.title;
  const description = props.description ?? DEFAULTS.description;
  const primaryCTA = props.primaryCTA ?? DEFAULTS.primaryCTA;
  const primaryHref = props.primaryHref ?? DEFAULTS.primaryHref;
  const phone = props.phone ?? DEFAULTS.phone;

  const phoneDigits = phone.replace(/\D/g, "");

  return (
    <section className="py-24 md:py-32">
      <div className="max-w-4xl mx-auto px-4 md:px-6">
        <FadeIn>
          <div className="relative rounded-2xl overflow-hidden">
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-accent/10 to-primary/5" />
            <div className="absolute inset-0 border border-primary/20 rounded-2xl" />

            <div className="relative px-8 py-16 md:px-16 md:py-20 text-center">
              <h2 className="text-3xl md:text-5xl font-heading font-bold">
                {title}
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-xl mx-auto">
                {description}
              </p>

              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
                <MagneticHover>
                  <Link
                    href={primaryHref}
                    className="group flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/25 cursor-pointer"
                  >
                    {primaryCTA}
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </MagneticHover>

                <Link
                  href={`tel:+1${phoneDigits}`}
                  className="text-muted-foreground hover:text-foreground transition-colors font-medium cursor-pointer"
                >
                  Or call {phone}
                </Link>
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

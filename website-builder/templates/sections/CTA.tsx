"use client";
import { ArrowRight } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";
import { MagneticHover } from "@/components/animations/MagneticHover";
import Link from "next/link";

// UPDATE: Replace CTA content with client's primary action

export function CTA() {
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
                {/* UPDATE: Replace with client's CTA headline */}
                Ready to Get Started?
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-xl mx-auto">
                {/* UPDATE: Replace with compelling reason to act now */}
                Contact us today for a free consultation. No obligation, no pressure —
                just honest advice from experts who care.
              </p>

              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
                <MagneticHover>
                  <Link
                    href="/contact"
                    className="group flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/25 cursor-pointer"
                  >
                    {/* UPDATE: Primary CTA text */}
                    Get Your Free Quote
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </MagneticHover>

                <Link
                  href="tel:+15550000000"
                  className="text-muted-foreground hover:text-foreground transition-colors font-medium cursor-pointer"
                >
                  {/* UPDATE: Client's phone number */}
                  Or call (555) 000-0000
                </Link>
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

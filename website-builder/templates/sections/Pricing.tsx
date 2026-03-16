"use client";
import { useState } from "react";
import { Check } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { FadeIn } from "@/components/animations/FadeIn";
import { cn } from "@/lib/utils";

// UPDATE: Replace with client's actual pricing tiers
const tiers = [
  {
    name: "Basic",
    price: { monthly: 49, annual: 39 },
    description: "Perfect for getting started",
    features: [
      "Feature one",
      "Feature two",
      "Feature three",
    ],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Professional",
    price: { monthly: 99, annual: 79 },
    description: "Best for growing businesses",
    features: [
      "Everything in Basic",
      "Feature four",
      "Feature five",
      "Feature six",
      "Priority support",
    ],
    cta: "Get Started",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: { monthly: 199, annual: 159 },
    description: "For large-scale operations",
    features: [
      "Everything in Professional",
      "Feature seven",
      "Feature eight",
      "Dedicated account manager",
      "Custom integrations",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

export function Pricing() {
  const [annual, setAnnual] = useState(false);
  const prefersReduced = useReducedMotion();

  return (
    <section className="py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        {/* Header */}
        <FadeIn className="text-center max-w-2xl mx-auto mb-12">
          <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
            Pricing
          </p>
          <h2 className="text-3xl md:text-5xl font-heading font-bold">
            Simple, Transparent{" "}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Pricing
            </span>
          </h2>
        </FadeIn>

        {/* Toggle */}
        <FadeIn delay={0.1} className="flex items-center justify-center gap-3 mb-16">
          <span className={cn("text-sm font-medium", !annual ? "text-foreground" : "text-muted-foreground")}>
            Monthly
          </span>
          <button
            onClick={() => setAnnual(!annual)}
            className={cn(
              "relative w-14 h-7 rounded-full transition-colors cursor-pointer",
              annual ? "bg-primary" : "bg-muted"
            )}
            aria-label={`Switch to ${annual ? "monthly" : "annual"} billing`}
          >
            <motion.div
              className="absolute top-1 w-5 h-5 rounded-full bg-white"
              animate={{ left: annual ? 32 : 4 }}
              transition={{ type: "spring", damping: 20, stiffness: 300 }}
            />
          </button>
          <span className={cn("text-sm font-medium", annual ? "text-foreground" : "text-muted-foreground")}>
            Annual
            <span className="ml-1.5 text-xs text-primary font-semibold">Save 20%</span>
          </span>
        </FadeIn>

        {/* Cards */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.1 } },
          }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8"
        >
          {tiers.map((tier, i) => (
            <motion.div
              key={i}
              variants={
                prefersReduced
                  ? {}
                  : {
                      hidden: { opacity: 0, y: 20 },
                      visible: { opacity: 1, y: 0, transition: { type: "spring", damping: 25, stiffness: 120 } },
                    }
              }
              className={cn(
                "relative p-8 rounded-xl border flex flex-col",
                tier.highlighted
                  ? "bg-card border-primary/50 shadow-lg shadow-primary/10"
                  : "bg-card border-border"
              )}
            >
              {tier.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-primary-foreground text-xs font-semibold rounded-full">
                  Most Popular
                </div>
              )}

              <h3 className="text-lg font-heading font-semibold">{tier.name}</h3>
              <p className="text-sm text-muted-foreground mt-1">{tier.description}</p>

              <div className="mt-6 mb-6">
                <span className="text-4xl font-heading font-bold">
                  ${annual ? tier.price.annual : tier.price.monthly}
                </span>
                <span className="text-muted-foreground">/mo</span>
              </div>

              <ul className="space-y-3 flex-grow">
                {tier.features.map((feature, j) => (
                  <li key={j} className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <span className="text-muted-foreground">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                className={cn(
                  "mt-8 w-full py-3 rounded-lg font-semibold transition-colors cursor-pointer",
                  tier.highlighted
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "bg-secondary text-foreground hover:bg-secondary/80"
                )}
              >
                {tier.cta}
              </button>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

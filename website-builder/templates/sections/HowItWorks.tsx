"use client";
import { FadeIn } from "@/components/animations/FadeIn";
import { FileText, Phone, ShieldCheck, type LucideIcon } from "lucide-react";

export interface Step {
  icon?: LucideIcon;
  number: string;
  title: string;
  description: string;
}

export interface HowItWorksProps {
  eyebrow?: string;
  title?: string;
  subtitle?: string;
  steps?: Step[];
}

// REPLACE: These defaults are intentionally generic. Pass real steps via props.
const defaultSteps: Step[] = [
  {
    icon: FileText,
    number: "01",
    title: "REPLACE: First Step Title",
    description: "REPLACE: Describe what the customer does in step 1. Be specific about what information they provide and how long it takes.",
  },
  {
    icon: Phone,
    number: "02",
    title: "REPLACE: Second Step Title",
    description: "REPLACE: Describe what happens next. What does your team do? How long does it take? What does the customer receive?",
  },
  {
    icon: ShieldCheck,
    number: "03",
    title: "REPLACE: Third Step Title",
    description: "REPLACE: Describe the outcome. What does the customer get? How quickly? What can they do next?",
  },
];

export function HowItWorks({
  eyebrow = "Simple Process",
  title = "REPLACE: How It Works",
  subtitle = "REPLACE: Brief description of your process.",
  steps = defaultSteps,
}: HowItWorksProps) {
  return (
    <section className="py-24 md:py-32 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <FadeIn className="text-center mb-16">
          <p className="text-sm font-semibold text-primary uppercase tracking-widest mb-3">
            {eyebrow}
          </p>
          <h2 className="text-3xl md:text-5xl font-heading font-bold">
            {title}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            {subtitle}
          </p>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-6 relative">
          {/* Connector line (desktop only) */}
          <div className="hidden md:block absolute top-24 left-[20%] right-[20%] h-px bg-gradient-to-r from-primary/30 via-primary/60 to-primary/30" />

          {steps.map((step, i) => {
            const Icon = step.icon || FileText;
            return (
              <FadeIn key={i} delay={i * 0.15}>
                <div className="relative text-center p-8">
                  <div className="relative inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 mb-6">
                    <Icon className="w-9 h-9 text-primary" />
                    <span className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">
                      {step.number}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
              </FadeIn>
            );
          })}
        </div>
      </div>
    </section>
  );
}

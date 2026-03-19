"use client";
import { motion, useReducedMotion } from "motion/react";
import { ArrowRight, Phone } from "lucide-react";
import Link from "next/link";

type HeroLayout = "centered" | "split-right" | "split-left";

interface HeroProps {
  title?: string;
  titleAccent?: string;
  subtitle?: string;
  badge?: string;
  primaryCTA?: string;
  primaryHref?: string;
  secondaryCTA?: string;
  secondaryHref?: string;
  /** Phone number for service businesses — renders prominently as a tel: link */
  phone?: string;
  /**
   * Layout variant:
   * - "centered" (default): text centered, no split panel
   * - "split-right": text on left, image placeholder on right
   * - "split-left": image placeholder on left, text on right
   */
  layout?: HeroLayout;
  /** Optional image URL for split layouts — shown in the graphic panel */
  heroImage?: string;
  /** Alt text for heroImage */
  heroImageAlt?: string;
}

// REPLACE: Pass real content via props. These defaults are flagged by the quality gate.
const DEFAULTS = {
  title: "REPLACE: Your Headline That",
  titleAccent: " Communicates Value",
  subtitle:
    "A clear, benefit-focused description that tells visitors exactly what you do and why they should care. Keep it under two lines.",
  badge: "Now accepting new clients",
  primaryCTA: "Get a Free Quote",
  primaryHref: "/contact",
  secondaryCTA: "View Our Services",
  secondaryHref: "/services",
};

function fade(delay: number, prefersReduced: boolean | null) {
  return {
    initial: prefersReduced ? false : { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { delay, type: "spring" as const, damping: 25, stiffness: 120 },
  };
}

export function Hero(props: HeroProps) {
  const prefersReduced = useReducedMotion();

  const title = props.title ?? DEFAULTS.title;
  const titleAccent = props.titleAccent ?? DEFAULTS.titleAccent;
  const subtitle = props.subtitle ?? DEFAULTS.subtitle;
  const badge = props.badge ?? DEFAULTS.badge;
  const primaryCTA = props.primaryCTA ?? DEFAULTS.primaryCTA;
  const primaryHref = props.primaryHref ?? DEFAULTS.primaryHref;
  const secondaryCTA = props.secondaryCTA ?? DEFAULTS.secondaryCTA;
  const secondaryHref = props.secondaryHref ?? DEFAULTS.secondaryHref;
  const layout = props.layout ?? "centered";

  const textBlock = (
    <div className={layout === "centered" ? "text-center max-w-3xl mx-auto" : "text-left"}>
      {/* Badge / Eyebrow */}
      {badge && (
        <motion.div {...fade(0.1, prefersReduced)} className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 rounded-full border border-border bg-card text-sm text-muted-foreground">
          <span className="w-2 h-2 rounded-full bg-primary" />
          {badge}
        </motion.div>
      )}

      {/* Headline */}
      <motion.h1
        {...fade(0.2, prefersReduced)}
        className="text-4xl sm:text-5xl md:text-6xl font-heading font-bold leading-tight tracking-tight text-foreground"
      >
        {title}
        {titleAccent && (
          <span className="text-primary">{titleAccent}</span>
        )}
      </motion.h1>

      {/* Subheading */}
      <motion.p
        {...fade(0.35, prefersReduced)}
        className="mt-5 text-lg md:text-xl text-muted-foreground leading-relaxed"
      >
        {subtitle}
      </motion.p>

      {/* Phone number — prominent for service businesses */}
      {props.phone && (
        <motion.div {...fade(0.45, prefersReduced)} className="mt-6">
          <a
            href={`tel:${props.phone.replace(/\D/g, "")}`}
            className="inline-flex items-center gap-2 text-2xl font-bold text-primary hover:text-primary/80 transition-colors"
            aria-label={`Call us at ${props.phone}`}
          >
            <Phone className="w-6 h-6" />
            {props.phone}
          </a>
          <p className="mt-1 text-sm text-muted-foreground">Call or text — free estimates</p>
        </motion.div>
      )}

      {/* CTA Buttons */}
      <motion.div
        {...fade(0.5, prefersReduced)}
        className={`mt-8 flex flex-col sm:flex-row gap-4 ${layout === "centered" ? "items-center justify-center" : "items-start"}`}
      >
        <Link
          href={primaryHref}
          className="group inline-flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-all shadow-md cursor-pointer"
        >
          {primaryCTA}
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </Link>

        {secondaryCTA && (
          <Link
            href={secondaryHref}
            className="inline-flex items-center gap-2 px-8 py-4 border border-border text-foreground font-semibold rounded-xl hover:bg-card transition-colors cursor-pointer"
          >
            {secondaryCTA}
          </Link>
        )}
      </motion.div>
    </div>
  );

  const graphicPanel = (
    <motion.div
      initial={prefersReduced ? false : { opacity: 0, x: layout === "split-right" ? 30 : -30 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3, type: "spring", damping: 25, stiffness: 100 }}
      className="relative rounded-2xl overflow-hidden bg-card border border-border aspect-[4/3] w-full"
    >
      {props.heroImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={props.heroImage}
          alt={props.heroImageAlt ?? ""}
          className="w-full h-full object-cover"
        />
      ) : (
        /* Placeholder — replace with real photo before launch */
        <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-muted-foreground bg-muted">
          <svg className="w-12 h-12 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span className="text-xs"><!-- CLIENT: Replace with a real photo --></span>
        </div>
      )}
    </motion.div>
  );

  if (layout === "centered") {
    return (
      <section className="relative bg-background py-24 md:py-32 overflow-hidden">
        <div className="relative z-10 max-w-5xl mx-auto px-4 md:px-6">
          {textBlock}
        </div>
      </section>
    );
  }

  return (
    <section className="relative bg-background py-20 md:py-28 overflow-hidden">
      <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-6">
        <div className={`grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center ${layout === "split-left" ? "lg:[&>*:first-child]:order-last" : ""}`}>
          {layout === "split-right" ? (
            <>
              {textBlock}
              {graphicPanel}
            </>
          ) : (
            <>
              {graphicPanel}
              {textBlock}
            </>
          )}
        </div>
      </div>
    </section>
  );
}

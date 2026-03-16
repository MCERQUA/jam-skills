"use client";
import { motion, useReducedMotion } from "motion/react";
import { ArrowRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

interface HeroSplitStat {
  value: string;
  label: string;
}

interface HeroSplitProps {
  title?: string;
  titleAccent?: string;
  subtitle?: string;
  badge?: string;
  primaryCTA?: string;
  primaryHref?: string;
  secondaryCTA?: string;
  secondaryHref?: string;
  image?: string;
  imageAlt?: string;
  stats?: HeroSplitStat[];
}

const DEFAULTS = {
  title: "Professional Service",
  titleAccent: " You Can Trust",
  subtitle:
    "A benefit-focused description that explains what you do and the value you deliver. Two lines max.",
  badge: "Trusted by 500+ clients",
  primaryCTA: "Get Started",
  primaryHref: "/contact",
  secondaryCTA: "Learn More",
  secondaryHref: "/about",
  image: "/images/hero.webp",
  imageAlt: "Description of hero image",
};

export function HeroSplit(props: HeroSplitProps) {
  const prefersReduced = useReducedMotion();

  const title = props.title ?? DEFAULTS.title;
  const titleAccent = props.titleAccent ?? DEFAULTS.titleAccent;
  const subtitle = props.subtitle ?? DEFAULTS.subtitle;
  const badge = props.badge ?? DEFAULTS.badge;
  const primaryCTA = props.primaryCTA ?? DEFAULTS.primaryCTA;
  const primaryHref = props.primaryHref ?? DEFAULTS.primaryHref;
  const secondaryCTA = props.secondaryCTA ?? DEFAULTS.secondaryCTA;
  const secondaryHref = props.secondaryHref ?? DEFAULTS.secondaryHref;
  const image = props.image ?? DEFAULTS.image;
  const imageAlt = props.imageAlt ?? DEFAULTS.imageAlt;

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-card/50" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-6 py-32 grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        {/* Text Column */}
        <div>
          <motion.div
            initial={prefersReduced ? false : { opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1, type: "spring", damping: 25, stiffness: 120 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 rounded-full border border-border bg-card/50 text-sm text-muted-foreground"
          >
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            {badge}
          </motion.div>

          <motion.h1
            initial={prefersReduced ? false : { opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, type: "spring", damping: 25, stiffness: 120 }}
            className="text-4xl sm:text-5xl md:text-6xl font-heading font-bold leading-tight"
          >
            {title}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {titleAccent}
            </span>
          </motion.h1>

          <motion.p
            initial={prefersReduced ? false : { opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.35, type: "spring", damping: 25, stiffness: 120 }}
            className="mt-6 text-lg text-muted-foreground leading-relaxed max-w-lg"
          >
            {subtitle}
          </motion.p>

          <motion.div
            initial={prefersReduced ? false : { opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, type: "spring", damping: 25, stiffness: 120 }}
            className="mt-8 flex flex-wrap gap-4"
          >
            <Link
              href={primaryHref}
              className="group flex items-center gap-2 px-7 py-3.5 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 cursor-pointer"
            >
              {primaryCTA}
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href={secondaryHref}
              className="px-7 py-3.5 border border-border text-foreground font-semibold rounded-xl hover:bg-card transition-colors cursor-pointer"
            >
              {secondaryCTA}
            </Link>
          </motion.div>
        </div>

        {/* Image Column */}
        <motion.div
          initial={prefersReduced ? false : { opacity: 0, x: 30, scale: 0.95 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          transition={{ delay: 0.3, type: "spring", damping: 25, stiffness: 100 }}
          className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-border shadow-2xl"
        >
          <Image
            src={image}
            alt={imageAlt}
            fill
            className="object-cover"
            priority
          />
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-background/40 to-transparent" />
        </motion.div>
      </div>
    </section>
  );
}

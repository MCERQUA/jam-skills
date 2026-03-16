"use client";
import { motion, useReducedMotion } from "motion/react";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

// UPDATE: Replace all content with client's brand intake answers

export function Hero() {
  const prefersReduced = useReducedMotion();

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background layers */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background to-card" />

      {/* Floating orbs (ambient depth) */}
      {!prefersReduced && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <motion.div
            className="absolute w-[500px] h-[500px] rounded-full bg-primary/8 blur-[100px]"
            animate={{
              x: [0, 30, -20, 0],
              y: [0, -40, 20, 0],
              scale: [1, 1.1, 0.95, 1],
            }}
            transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
            style={{ top: "10%", left: "15%" }}
          />
          <motion.div
            className="absolute w-[400px] h-[400px] rounded-full bg-accent/6 blur-[100px]"
            animate={{
              x: [0, -25, 35, 0],
              y: [0, 30, -25, 0],
              scale: [1, 0.9, 1.1, 1],
            }}
            transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
            style={{ bottom: "15%", right: "10%" }}
          />
        </div>
      )}

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 md:px-6 text-center">
        {/* Badge / Eyebrow */}
        <motion.div
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, type: "spring", damping: 25, stiffness: 120 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 rounded-full border border-border bg-card/50 text-sm text-muted-foreground"
        >
          {/* UPDATE: Replace with client's tagline or announcement */}
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          Now accepting new clients
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, type: "spring", damping: 25, stiffness: 120 }}
          className="text-4xl sm:text-5xl md:text-7xl font-heading font-bold leading-tight tracking-tight"
        >
          {/* UPDATE: Replace with client's primary headline */}
          Your Headline That
          <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            {" "}Communicates Value
          </span>
        </motion.h1>

        {/* Subheading */}
        <motion.p
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, type: "spring", damping: 25, stiffness: 120 }}
          className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed"
        >
          {/* UPDATE: Replace with 1-2 sentence description from brand intake */}
          A clear, benefit-focused description that tells visitors exactly what
          you do and why they should care. Keep it under two lines.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, type: "spring", damping: 25, stiffness: 120 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          {/* Primary CTA */}
          <Link
            href="/contact"
            className="group flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 cursor-pointer"
          >
            {/* UPDATE: Replace with client's primary CTA */}
            Get a Free Quote
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>

          {/* Secondary CTA */}
          <Link
            href="/services"
            className="px-8 py-4 border border-border text-foreground font-semibold rounded-xl hover:bg-card transition-colors cursor-pointer"
          >
            {/* UPDATE: Replace with client's secondary action */}
            View Our Services
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

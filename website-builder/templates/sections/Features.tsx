"use client";
import { motion, useReducedMotion } from "motion/react";
import { Shield, Zap, Heart, Clock, Award, Users } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";

// UPDATE: Replace features with client's actual features/benefits
const features = [
  {
    icon: Shield,
    title: "Reliable Service",
    description: "Consistent quality you can count on, backed by our satisfaction guarantee.",
  },
  {
    icon: Zap,
    title: "Fast Response",
    description: "Quick turnaround times so you're never left waiting.",
  },
  {
    icon: Heart,
    title: "Customer First",
    description: "Every decision we make starts with what's best for you.",
  },
  {
    icon: Clock,
    title: "Available 24/7",
    description: "Round-the-clock support whenever you need us.",
  },
  {
    icon: Award,
    title: "Industry Experts",
    description: "Years of experience delivering top-tier results.",
  },
  {
    icon: Users,
    title: "Trusted Team",
    description: "Vetted professionals who treat your project like their own.",
  },
];

export function Features() {
  const prefersReduced = useReducedMotion();

  const stagger = 0.08;

  return (
    <section className="py-24 md:py-32 bg-card/30">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        {/* Section Header */}
        <FadeIn className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
            {/* UPDATE: Section label */}
            Why Choose Us
          </p>
          <h2 className="text-3xl md:text-5xl font-heading font-bold">
            {/* UPDATE: Section heading */}
            Everything You Need,{" "}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Nothing You Don&apos;t
            </span>
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            {/* UPDATE: Section description */}
            We focus on what matters most to deliver real results for your business.
          </p>
        </FadeIn>

        {/* Feature Grid */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: stagger } },
          }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8"
        >
          {features.map((feature, i) => (
            <motion.div
              key={i}
              variants={
                prefersReduced
                  ? {}
                  : {
                      hidden: { opacity: 0, y: 20 },
                      visible: {
                        opacity: 1,
                        y: 0,
                        transition: {
                          type: "spring",
                          damping: 25,
                          stiffness: 120,
                        },
                      },
                    }
              }
              whileHover={prefersReduced ? {} : { y: -4 }}
              className="group p-8 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors cursor-pointer"
            >
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-5 group-hover:bg-primary/20 transition-colors">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-heading font-semibold mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

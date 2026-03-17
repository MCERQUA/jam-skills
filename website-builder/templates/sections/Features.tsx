"use client";
import { motion, useReducedMotion } from "motion/react";
import { Shield, Zap, Heart, Clock, Award, Users, type LucideIcon } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";

const iconMap: Record<string, LucideIcon> = {
  shield: Shield,
  zap: Zap,
  heart: Heart,
  clock: Clock,
  award: Award,
  users: Users,
};

interface FeatureItem {
  icon: string;
  title: string;
  description: string;
}

interface FeaturesProps {
  title?: string;
  titleAccent?: string;
  subtitle?: string;
  label?: string;
  features?: FeatureItem[];
}

// REPLACE: Pass real features via props. These defaults are flagged by the quality gate.
const DEFAULT_FEATURES: FeatureItem[] = [
  {
    icon: "shield",
    title: "REPLACE: Feature Title",
    description: "REPLACE: Specific description of this feature/service for this business.",
  },
  {
    icon: "zap",
    title: "REPLACE: Feature Title",
    description: "REPLACE: Specific description with industry-relevant details.",
  },
  {
    icon: "heart",
    title: "REPLACE: Feature Title",
    description: "REPLACE: Benefit-focused description. What does the customer get?",
  },
  {
    icon: "clock",
    title: "REPLACE: Feature Title",
    description: "REPLACE: Include specific numbers or timeframes if applicable.",
  },
  {
    icon: "award",
    title: "REPLACE: Feature Title",
    description: "REPLACE: Describe concrete expertise or qualifications.",
  },
  {
    icon: "users",
    title: "REPLACE: Feature Title",
    description: "REPLACE: What makes this team/service different? Be specific.",
  },
];

const DEFAULTS = {
  label: "Why Choose Us",
  title: "Everything You Need, ",
  titleAccent: "Nothing You Don\u2019t",
  subtitle: "We focus on what matters most to deliver real results for your business.",
};

export function Features(props: FeaturesProps) {
  const prefersReduced = useReducedMotion();

  const label = props.label ?? DEFAULTS.label;
  const title = props.title ?? DEFAULTS.title;
  const titleAccent = props.titleAccent ?? DEFAULTS.titleAccent;
  const subtitle = props.subtitle ?? DEFAULTS.subtitle;
  const features = props.features ?? DEFAULT_FEATURES;

  const stagger = 0.08;

  return (
    <section className="py-24 md:py-32 bg-card/30">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        {/* Section Header */}
        <FadeIn className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
            {label}
          </p>
          <h2 className="text-3xl md:text-5xl font-heading font-bold">
            {title}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {titleAccent}
            </span>
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            {subtitle}
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
          {features.map((feature, i) => {
            const Icon = iconMap[feature.icon] ?? Shield;
            return (
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
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-heading font-semibold mb-2">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}

"use client";
import { motion, useReducedMotion } from "motion/react";
import { Shield, Zap, Heart, Award } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";
import { cn } from "@/lib/utils";

// UPDATE: Replace with client's features. Bento grid works best with 4-6 items.
const features = [
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "Bank-level encryption and security protocols protect your data at every step.",
    span: "col-span-1 md:col-span-2", // Wide card
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Sub-second response times powered by edge computing.",
    span: "col-span-1",
  },
  {
    icon: Heart,
    title: "Built with Care",
    description: "Every detail crafted with attention to user experience.",
    span: "col-span-1",
  },
  {
    icon: Award,
    title: "Award-Winning Support",
    description: "Our team has been recognized for outstanding customer service and dedication.",
    span: "col-span-1 md:col-span-2", // Wide card
  },
];

export function FeaturesBento() {
  const prefersReduced = useReducedMotion();

  return (
    <section className="py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        <FadeIn className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
            Features
          </p>
          <h2 className="text-3xl md:text-5xl font-heading font-bold">
            Built for{" "}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Modern Business
            </span>
          </h2>
        </FadeIn>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.08 } },
          }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6"
        >
          {features.map((feature, i) => (
            <motion.div
              key={i}
              variants={
                prefersReduced
                  ? {}
                  : {
                      hidden: { opacity: 0, y: 20, scale: 0.98 },
                      visible: {
                        opacity: 1, y: 0, scale: 1,
                        transition: { type: "spring", damping: 25, stiffness: 120 },
                      },
                    }
              }
              whileHover={prefersReduced ? {} : { y: -4 }}
              className={cn(
                "group relative p-8 md:p-10 rounded-xl bg-card border border-border overflow-hidden cursor-pointer transition-colors hover:border-primary/30",
                feature.span
              )}
            >
              {/* Gradient hover glow */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-5 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-heading font-semibold mb-2">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

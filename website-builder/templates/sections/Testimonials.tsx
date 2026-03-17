"use client";
import { Star } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";
import { StaggerChildren, StaggerItem } from "@/components/animations/StaggerChildren";

interface TestimonialItem {
  name: string;
  role: string;
  text: string;
  rating?: number;
}

interface TestimonialsProps {
  title?: string;
  titleAccent?: string;
  label?: string;
  testimonials?: TestimonialItem[];
}

// REPLACE: Pass real testimonials via props. These defaults are intentionally flagged.
const DEFAULT_TESTIMONIALS: TestimonialItem[] = [
  {
    name: "REPLACE: Full Name",
    role: "REPLACE: Role, Company Name, Location",
    text: "REPLACE: Specific testimonial referencing a real service or outcome. Not generic praise. Include details about what they liked and what the result was.",
    rating: 5,
  },
  {
    name: "REPLACE: Full Name",
    role: "REPLACE: Role, Company Name, Location",
    text: "REPLACE: Another testimonial with different focus (price, speed, quality). Reference specific services by name.",
    rating: 5,
  },
  {
    name: "REPLACE: Full Name",
    role: "REPLACE: Role, Company Name, Location",
    text: "REPLACE: Third testimonial with unique angle. Include a specific result or number if possible.",
    rating: 5,
  },
];

const DEFAULTS = {
  label: "Testimonials",
  title: "What Our ",
  titleAccent: "Clients Say",
};

export function Testimonials(props: TestimonialsProps) {
  const label = props.label ?? DEFAULTS.label;
  const title = props.title ?? DEFAULTS.title;
  const titleAccent = props.titleAccent ?? DEFAULTS.titleAccent;
  const testimonials = props.testimonials ?? DEFAULT_TESTIMONIALS;

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
        </FadeIn>

        {/* Testimonial Cards */}
        <StaggerChildren className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {testimonials.map((testimonial, i) => (
            <StaggerItem key={i}>
              <div className="p-8 rounded-xl bg-card border border-border h-full flex flex-col">
                {/* Stars */}
                <div className="flex gap-1 mb-4">
                  {Array.from({ length: testimonial.rating ?? 5 }).map((_, j) => (
                    <Star key={j} className="w-4 h-4 fill-primary text-primary" />
                  ))}
                </div>

                {/* Quote */}
                <p className="text-foreground leading-relaxed flex-grow">
                  &ldquo;{testimonial.text}&rdquo;
                </p>

                {/* Author */}
                <div className="mt-6 pt-4 border-t border-border">
                  <p className="font-semibold text-sm">{testimonial.name}</p>
                  <p className="text-xs text-muted-foreground">{testimonial.role}</p>
                </div>
              </div>
            </StaggerItem>
          ))}
        </StaggerChildren>
      </div>
    </section>
  );
}

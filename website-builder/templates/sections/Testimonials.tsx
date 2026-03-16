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

const DEFAULT_TESTIMONIALS: TestimonialItem[] = [
  {
    name: "Sarah Johnson",
    role: "Homeowner",
    text: "Absolutely outstanding service. They went above and beyond to make sure everything was perfect. Highly recommend to anyone looking for quality work.",
    rating: 5,
  },
  {
    name: "Mike Chen",
    role: "Business Owner",
    text: "Professional, punctual, and reasonably priced. They've been our go-to for over three years now. Wouldn't trust anyone else.",
    rating: 5,
  },
  {
    name: "Lisa Rodriguez",
    role: "Property Manager",
    text: "Fast response times and excellent communication throughout the entire process. The team really knows what they're doing.",
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

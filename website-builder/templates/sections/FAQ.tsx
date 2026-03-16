"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ChevronDown } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";

interface FAQItem {
  question: string;
  answer: string;
}

export interface FAQProps {
  eyebrow?: string;
  title?: string;
  subtitle?: string;
  faqs?: FAQItem[];
}

// REPLACE: These defaults are intentionally generic. You MUST pass real FAQ content via props.
const defaultFAQs: FAQItem[] = [
  {
    question: "REPLACE: First frequently asked question targeting a long-tail keyword?",
    answer: "REPLACE: Comprehensive answer with industry-specific details. 3-5 sentences minimum. Include specific numbers, timeframes, or requirements.",
  },
  {
    question: "REPLACE: Second question matching a real Google search?",
    answer: "REPLACE: Detailed answer demonstrating expertise. Reference specific services, costs, or processes.",
  },
  {
    question: "REPLACE: Third question about costs or requirements?",
    answer: "REPLACE: Answer with real numbers — cost ranges, timeframes, steps involved.",
  },
];

function FAQAccordion({ item, isOpen, onToggle }: { item: FAQItem; isOpen: boolean; onToggle: () => void }) {
  return (
    <div className="border border-border rounded-xl overflow-hidden bg-background hover:border-primary/30 transition-colors">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left cursor-pointer"
      >
        <span className="font-semibold text-lg">{item.question}</span>
        <ChevronDown
          className={`w-5 h-5 text-muted-foreground shrink-0 transition-transform duration-300 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="px-6 pb-5 text-muted-foreground leading-relaxed">
              {item.answer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function FAQ({
  eyebrow = "Common Questions",
  title = "REPLACE: Frequently Asked Questions",
  subtitle = "REPLACE: Subtitle describing what questions are answered here.",
  faqs = defaultFAQs,
}: FAQProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="py-24 md:py-32 bg-card/30">
      <div className="max-w-4xl mx-auto px-4 md:px-6">
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

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <FadeIn key={i} delay={i * 0.05}>
              <FAQAccordion
                item={faq}
                isOpen={openIndex === i}
                onToggle={() => setOpenIndex(openIndex === i ? null : i)}
              />
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

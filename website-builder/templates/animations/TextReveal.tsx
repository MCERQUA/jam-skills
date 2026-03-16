"use client";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils";

interface TextRevealProps {
  text: string;
  className?: string;
  /** "word" reveals word by word, "character" reveals character by character */
  mode?: "word" | "character";
  /** Delay between each unit in seconds. Default: 0.08 */
  stagger?: number;
}

export function TextReveal({
  text,
  className,
  mode = "word",
  stagger = 0.08,
}: TextRevealProps) {
  const prefersReduced = useReducedMotion();
  const units = mode === "word" ? text.split(" ") : text.split("");
  const separator = mode === "word" ? " " : "";

  if (prefersReduced) {
    return <span className={cn(className)}>{text}</span>;
  }

  return (
    <motion.span
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className={cn(className)}
    >
      {units.map((unit, i) => (
        <motion.span
          key={i}
          className="inline-block"
          style={mode === "word" ? { marginRight: "0.25em" } : undefined}
          variants={{
            hidden: { opacity: 0, y: 10, filter: "blur(4px)" },
            visible: {
              opacity: 1,
              y: 0,
              filter: "blur(0px)",
              transition: {
                delay: i * stagger,
                type: "spring",
                damping: 25,
                stiffness: 120,
              },
            },
          }}
        >
          {unit}{separator}
        </motion.span>
      ))}
    </motion.span>
  );
}

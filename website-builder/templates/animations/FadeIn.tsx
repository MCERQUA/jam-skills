"use client";
import { motion, useReducedMotion, useInView } from "motion/react";
import { useRef, useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface FadeInProps {
  children: React.ReactNode;
  className?: string;
  /** Direction to slide from. Default: "up" */
  direction?: "up" | "down" | "left" | "right" | "none";
  /** Pixels to offset. Default: 30 */
  distance?: number;
  /** Delay in seconds. Default: 0 */
  delay?: number;
  /** Only animate once. Default: true */
  once?: boolean;
}

const directionMap = {
  up: { y: 1, x: 0 },
  down: { y: -1, x: 0 },
  left: { x: 1, y: 0 },
  right: { x: -1, y: 0 },
  none: { x: 0, y: 0 },
};

export function FadeIn({
  children,
  className,
  direction = "up",
  distance = 30,
  delay = 0,
  once = true,
}: FadeInProps) {
  const prefersReduced = useReducedMotion();
  const d = directionMap[direction];
  // SSR-safe: render visible by default, only set initial hidden state after hydration
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Before hydration: render children visible (no opacity:0 in SSR HTML)
  // After hydration: use motion animation
  if (!mounted || prefersReduced) {
    return <div className={cn(className)}>{children}</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: d.x * distance, y: d.y * distance }}
      whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once, margin: "-80px" }}
      transition={{
        type: "spring",
        damping: 25,
        stiffness: 120,
        delay,
      }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}

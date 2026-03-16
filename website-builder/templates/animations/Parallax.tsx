"use client";
import { useScroll, useTransform, motion, useReducedMotion } from "motion/react";
import { useRef } from "react";
import { cn } from "@/lib/utils";

interface ParallaxProps {
  children: React.ReactNode;
  className?: string;
  /** Pixels of offset in each direction. Default: 50 */
  offset?: number;
  /** Speed multiplier (1 = normal, 0.5 = half, 2 = double). Default: 1 */
  speed?: number;
}

export function Parallax({
  children,
  className,
  offset = 50,
  speed = 1,
}: ParallaxProps) {
  const prefersReduced = useReducedMotion();
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });
  const y = useTransform(
    scrollYProgress,
    [0, 1],
    [offset * speed, -offset * speed]
  );

  if (prefersReduced) {
    return <div className={cn(className)}>{children}</div>;
  }

  return (
    <motion.div ref={ref} style={{ y }} className={cn(className)}>
      {children}
    </motion.div>
  );
}

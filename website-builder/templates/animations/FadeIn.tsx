"use client";
import { motion, useReducedMotion } from "motion/react";
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

  return (
    <motion.div
      initial={
        prefersReduced
          ? false
          : { opacity: 0, x: d.x * distance, y: d.y * distance }
      }
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

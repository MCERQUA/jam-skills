"use client";
import { motion, useMotionValue, useSpring, useReducedMotion } from "motion/react";
import { useRef } from "react";
import { cn } from "@/lib/utils";

interface MagneticHoverProps {
  children: React.ReactNode;
  className?: string;
  /** How strongly the element follows the cursor (0-1). Default: 0.3 */
  strength?: number;
}

export function MagneticHover({
  children,
  className,
  strength = 0.3,
}: MagneticHoverProps) {
  const prefersReduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { damping: 20, stiffness: 200 });
  const springY = useSpring(y, { damping: 20, stiffness: 200 });

  if (prefersReduced) {
    return <div className={cn(className)}>{children}</div>;
  }

  const handleMouse = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    x.set((e.clientX - centerX) * strength);
    y.set((e.clientY - centerY) * strength);
  };

  const reset = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={reset}
      style={{ x: springX, y: springY }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}

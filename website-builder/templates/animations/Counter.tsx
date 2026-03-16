"use client";
import { useEffect, useRef, useState } from "react";
import { useInView, animate, useReducedMotion } from "motion/react";

interface CounterProps {
  /** Target number to count to */
  target: number;
  /** Suffix after the number (e.g., "+", "%", "k") */
  suffix?: string;
  /** Prefix before the number (e.g., "$") */
  prefix?: string;
  /** Animation duration in seconds. Default: 2 */
  duration?: number;
  /** Format with locale separators. Default: true */
  format?: boolean;
  className?: string;
}

export function Counter({
  target,
  suffix = "",
  prefix = "",
  duration = 2,
  format = true,
  className,
}: CounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const prefersReduced = useReducedMotion();
  const [value, setValue] = useState(prefersReduced ? target : 0);

  useEffect(() => {
    if (!isInView || prefersReduced) return;

    const controls = animate(0, target, {
      duration,
      ease: "easeOut",
      onUpdate: (v) => setValue(Math.round(v)),
    });

    return controls.stop;
  }, [isInView, target, duration, prefersReduced]);

  const display = format ? value.toLocaleString() : String(value);

  return (
    <span ref={ref} className={className}>
      {prefix}{display}{suffix}
    </span>
  );
}

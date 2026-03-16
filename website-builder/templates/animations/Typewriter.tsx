"use client";
import { useState, useEffect } from "react";
import { motion, useReducedMotion, useInView } from "motion/react";
import { useRef } from "react";

interface TypewriterProps {
  text: string;
  className?: string;
  /** Milliseconds per character. Default: 50 */
  speed?: number;
  /** Delay before starting in ms. Default: 0 */
  delay?: number;
  /** Show blinking cursor. Default: true */
  cursor?: boolean;
}

export function Typewriter({
  text,
  className,
  speed = 50,
  delay = 0,
  cursor = true,
}: TypewriterProps) {
  const prefersReduced = useReducedMotion();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const [displayed, setDisplayed] = useState(prefersReduced ? text : "");
  const [done, setDone] = useState(prefersReduced ?? false);

  useEffect(() => {
    if (prefersReduced || !isInView) return;

    const timeout = setTimeout(() => {
      let i = 0;
      const interval = setInterval(() => {
        setDisplayed(text.slice(0, i + 1));
        i++;
        if (i >= text.length) {
          clearInterval(interval);
          setDone(true);
        }
      }, speed);
      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timeout);
  }, [text, speed, delay, isInView, prefersReduced]);

  return (
    <span ref={ref} className={className}>
      {displayed}
      {cursor && !done && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
          className="inline-block ml-0.5"
        >
          |
        </motion.span>
      )}
    </span>
  );
}

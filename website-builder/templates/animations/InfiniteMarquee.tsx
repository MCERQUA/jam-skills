"use client";
import { useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils";

interface InfiniteMarqueeProps {
  children: React.ReactNode;
  className?: string;
  /** Duration of one full cycle in seconds. Default: 30 */
  speed?: number;
  /** Reverse direction. Default: false */
  reverse?: boolean;
  /** Pause on hover. Default: true */
  pauseOnHover?: boolean;
}

export function InfiniteMarquee({
  children,
  className,
  speed = 30,
  reverse = false,
  pauseOnHover = true,
}: InfiniteMarqueeProps) {
  const prefersReduced = useReducedMotion();

  if (prefersReduced) {
    return (
      <div className={cn("flex gap-8 overflow-hidden", className)}>
        {children}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "overflow-hidden",
        pauseOnHover && "group",
        className
      )}
    >
      <div
        className={cn(
          "flex gap-8 w-max",
          "animate-marquee",
          pauseOnHover && "group-hover:[animation-play-state:paused]",
          reverse && "[animation-direction:reverse]"
        )}
        style={{ "--marquee-speed": `${speed}s` } as React.CSSProperties}
      >
        {children}
        {children}
      </div>
    </div>
  );
}

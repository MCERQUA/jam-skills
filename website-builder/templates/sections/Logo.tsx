"use client";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

interface LogoProps {
  src?: string;
  alt?: string;
  width?: number;
  height?: number;
  href?: string;
  wordmarkFallback: string;
  className?: string;
}

/**
 * Brand logo with image-or-wordmark fallback.
 *
 * Phase 5 (ASSETS) of the website-build pipeline copies the client's logo to
 * `public/logo.png` (or `.svg`). This component renders it via `next/image`.
 * If `src` is missing or fails to load, it falls back to `wordmarkFallback`
 * styled as a heading — so the build never ships a blank header.
 */
export function Logo({
  src = "/logo.png",
  alt,
  width = 160,
  height = 40,
  href = "/",
  wordmarkFallback,
  className,
}: LogoProps) {
  const [errored, setErrored] = useState(false);

  const wordmark = (
    <span className="text-xl font-heading font-bold text-foreground tracking-tight">
      {wordmarkFallback}
    </span>
  );

  const content = !src || errored ? wordmark : (
    <Image
      src={src}
      alt={alt ?? wordmarkFallback}
      width={width}
      height={height}
      priority
      onError={() => setErrored(true)}
      className="h-8 md:h-10 w-auto object-contain"
    />
  );

  if (href) {
    return (
      <Link href={href} className={`shrink-0 inline-flex items-center ${className ?? ""}`} aria-label={wordmarkFallback}>
        {content}
      </Link>
    );
  }
  return <span className={`shrink-0 inline-flex items-center ${className ?? ""}`}>{content}</span>;
}

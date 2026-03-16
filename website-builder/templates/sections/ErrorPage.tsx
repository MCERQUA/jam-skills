"use client";

// Use this as src/app/error.tsx
// Must be a client component (Next.js requirement)

import { useEffect } from "react";
import { RefreshCw } from "lucide-react";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <p className="text-6xl font-heading font-bold text-destructive">
          Oops
        </p>
        <h1 className="mt-4 text-2xl font-heading font-bold">
          Something Went Wrong
        </h1>
        <p className="mt-3 text-muted-foreground">
          We hit an unexpected error. Please try again.
        </p>
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 mt-8 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      </div>
    </main>
  );
}

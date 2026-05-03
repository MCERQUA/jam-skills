import Link from "next/link";
import { ArrowLeft } from "lucide-react";

// Use this as src/app/not-found.tsx

export default function NotFound() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <p className="text-8xl font-heading font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          404
        </p>
        <h1 className="mt-4 text-2xl font-heading font-bold">
          Page Not Found
        </h1>
        <p className="mt-3 text-muted-foreground">
          Sorry, we couldn&apos;t find the page you&apos;re looking for.
          It might have been moved or no longer exists.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 mt-8 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </main>
  );
}

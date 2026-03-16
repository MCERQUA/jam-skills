import { Inter, Space_Grotesk } from "next/font/google";

// UPDATE: Replace with fonts from brand intake.
// See instructions/design-system.md for recommended pairings by tone.

export const bodyFont = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

export const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["500", "600", "700"],
  display: "swap",
});

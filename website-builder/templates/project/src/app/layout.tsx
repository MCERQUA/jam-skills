import type { Metadata } from "next";
import { headingFont, bodyFont } from "@/lib/fonts";
import { SmoothScroll } from "@/components/animations/SmoothScroll";
import "./globals.css";

// UPDATE: Replace with client's business info
export const metadata: Metadata = {
  metadataBase: new URL("https://www.example.com"),
  title: {
    default: "Business Name — What They Do",
    template: "%s | Business Name",
  },
  description: "Compelling 150-160 char description with primary keyword.",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://www.example.com",
    siteName: "Business Name",
    title: "Business Name — What They Do",
    description: "Compelling description for social sharing.",
    images: [
      {
        url: "/og/default.png",
        width: 1200,
        height: 630,
        alt: "Business Name",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Business Name — What They Do",
    description: "Compelling description for social sharing.",
    images: ["/og/default.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${headingFont.variable} ${bodyFont.variable}`}>
      <body className="antialiased">
        <SmoothScroll>
          {children}
        </SmoothScroll>
      </body>
    </html>
  );
}

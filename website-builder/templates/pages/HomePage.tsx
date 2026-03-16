// Home Page Composition Template
// Copy sections from templates/sections/ into src/components/sections/
// Then compose this page from them.

import { Navbar } from "@/components/sections/Navbar";
import { Hero } from "@/components/sections/Hero";
import { Features } from "@/components/sections/Features";
import { Stats } from "@/components/sections/Stats";
import { Testimonials } from "@/components/sections/Testimonials";
import { CTA } from "@/components/sections/CTA";
import { Footer } from "@/components/sections/Footer";

// Optional additions:
// import { InfiniteMarquee } from "@/components/animations/InfiniteMarquee";
// import { BlogList } from "@/components/sections/BlogList";
// import { Pricing } from "@/components/sections/Pricing";

export default function HomePage() {
  return (
    <main>
      <Navbar />
      <Hero />
      {/* Optional: Logo marquee between Hero and Features */}
      {/* <InfiniteMarquee speed={25}>
        <div className="flex items-center gap-16 px-8 py-6">
          client logos here
        </div>
      </InfiniteMarquee> */}
      <Features />
      <Stats />
      <Testimonials />
      {/* Optional: <Pricing /> */}
      {/* Optional: <BlogList /> */}
      <CTA />
      <Footer />
    </main>
  );
}

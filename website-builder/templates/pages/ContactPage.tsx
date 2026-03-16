// Contact Page Composition Template

import type { Metadata } from "next";
import { Navbar } from "@/components/sections/Navbar";
import { ContactForm } from "@/components/sections/ContactForm";
import { Footer } from "@/components/sections/Footer";

export const metadata: Metadata = {
  title: "Contact Us",
  description: "Get in touch with us for a free consultation. We respond within 24 hours.",
};

export default function ContactPage() {
  return (
    <main>
      <Navbar />
      {/* Add pt-20 to account for fixed navbar */}
      <div className="pt-20">
        <ContactForm />
      </div>
      <Footer />
    </main>
  );
}

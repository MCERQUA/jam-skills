// Contact Page Composition Template
//
// All section components accept optional props for customization.

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
      <Navbar
        logo="Acme Co"
        cta={{ label: "Get a Quote", href: "/contact" }}
      />

      {/* Add pt-20 to account for fixed navbar */}
      <div className="pt-20">
        <ContactForm
          title="Let's Talk About"
          titleAccent=" Your Project"
          subtitle="Fill out the form and we'll get back to you within 24 hours."
          email="hello@example.com"
          phone="(555) 000-0000"
          address="123 Main Street, City, ST 00000"
          fields={[
            { name: "name", label: "Name", type: "text", required: true, placeholder: "Your name" },
            { name: "email", label: "Email", type: "email", required: true, placeholder: "you@example.com" },
            { name: "phone", label: "Phone (optional)", type: "tel", required: false, placeholder: "(555) 000-0000" },
            { name: "service", label: "Service Needed", type: "text", required: false, placeholder: "e.g. Web Design" },
            { name: "message", label: "Message", type: "textarea", required: true, placeholder: "Tell us about your project..." },
          ]}
        />
      </div>

      <Footer
        businessName="Acme Co"
        phone="(555) 000-0000"
        email="hello@example.com"
        address="123 Main Street, City, ST 00000"
      />
    </main>
  );
}

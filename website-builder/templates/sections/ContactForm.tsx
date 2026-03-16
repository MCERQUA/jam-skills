"use client";
import { useState } from "react";
import { Send, CheckCircle, Phone, Mail, MapPin } from "lucide-react";
import { FadeIn } from "@/components/animations/FadeIn";

interface ContactField {
  name: string;
  label: string;
  type: string;
  required?: boolean;
  placeholder?: string;
}

interface ContactFormProps {
  title?: string;
  titleAccent?: string;
  subtitle?: string;
  email?: string;
  phone?: string;
  address?: string;
  fields?: ContactField[];
}

const DEFAULT_FIELDS: ContactField[] = [
  { name: "name", label: "Name", type: "text", required: true, placeholder: "Your name" },
  { name: "email", label: "Email", type: "email", required: true, placeholder: "you@example.com" },
  { name: "phone", label: "Phone (optional)", type: "tel", required: false, placeholder: "(555) 000-0000" },
  { name: "message", label: "Message", type: "textarea", required: true, placeholder: "Tell us about your project..." },
];

const DEFAULTS = {
  title: "Let\u2019s Talk About",
  titleAccent: " Your Project",
  subtitle:
    "Fill out the form and we\u2019ll get back to you within 24 hours. Or reach out directly \u2014 we\u2019re always happy to chat.",
  email: "hello@example.com",
  phone: "(555) 000-0000",
  address: "123 Main Street, City, ST 00000",
};

export function ContactForm(props: ContactFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const title = props.title ?? DEFAULTS.title;
  const titleAccent = props.titleAccent ?? DEFAULTS.titleAccent;
  const subtitle = props.subtitle ?? DEFAULTS.subtitle;
  const email = props.email ?? DEFAULTS.email;
  const phone = props.phone ?? DEFAULTS.phone;
  const address = props.address ?? DEFAULTS.address;
  const fields = props.fields ?? DEFAULT_FIELDS;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const formData = new FormData(e.currentTarget);

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.fromEntries(formData)),
      });

      if (!res.ok) {
        throw new Error("Failed to send message. Please try again.");
      }

      setIsSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isSubmitted) {
    return (
      <section className="py-24 md:py-32">
        <div className="max-w-2xl mx-auto px-4 md:px-6 text-center">
          <FadeIn>
            <CheckCircle className="w-16 h-16 text-primary mx-auto mb-6" />
            <h2 className="text-3xl font-heading font-bold">Thank You!</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              We&apos;ve received your message and will get back to you within 24 hours.
            </p>
          </FadeIn>
        </div>
      </section>
    );
  }

  return (
    <section className="py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16">
          {/* Info Column */}
          <FadeIn direction="left">
            <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-3">
              Contact Us
            </p>
            <h2 className="text-3xl md:text-5xl font-heading font-bold">
              {title}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                {titleAccent}
              </span>
            </h2>
            <p className="mt-4 text-lg text-muted-foreground leading-relaxed">
              {subtitle}
            </p>

            <div className="mt-8 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">Email</p>
                  <p className="text-sm text-muted-foreground">{email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Phone className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">Phone</p>
                  <p className="text-sm text-muted-foreground">{phone}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <MapPin className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">Address</p>
                  <p className="text-sm text-muted-foreground">{address}</p>
                </div>
              </div>
            </div>
          </FadeIn>

          {/* Form Column */}
          <FadeIn direction="right" delay={0.15}>
            <form onSubmit={handleSubmit} className="space-y-6">
              {renderFields(fields)}

              {error && (
                <p className="text-sm text-red-500">{error}</p>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    Send Message
                    <Send className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </FadeIn>
        </div>
      </div>
    </section>
  );
}

function renderFields(fields: ContactField[]) {
  // Group non-textarea fields into pairs for the 2-column layout
  const textareaFields = fields.filter((f) => f.type === "textarea");
  const inlineFields = fields.filter((f) => f.type !== "textarea");

  const rows: ContactField[][] = [];
  for (let i = 0; i < inlineFields.length; i += 2) {
    rows.push(inlineFields.slice(i, i + 2));
  }

  return (
    <>
      {rows.map((row, ri) => (
        <div key={ri} className={row.length > 1 ? "grid grid-cols-1 sm:grid-cols-2 gap-4" : ""}>
          {row.map((field) => (
            <div key={field.name}>
              <label htmlFor={field.name} className="block text-sm font-medium mb-2">
                {field.label}
              </label>
              <input
                id={field.name}
                name={field.name}
                type={field.type}
                required={field.required}
                className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                placeholder={field.placeholder}
              />
            </div>
          ))}
        </div>
      ))}
      {textareaFields.map((field) => (
        <div key={field.name}>
          <label htmlFor={field.name} className="block text-sm font-medium mb-2">
            {field.label}
          </label>
          <textarea
            id={field.name}
            name={field.name}
            required={field.required}
            rows={5}
            className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors resize-none"
            placeholder={field.placeholder}
          />
        </div>
      ))}
    </>
  );
}

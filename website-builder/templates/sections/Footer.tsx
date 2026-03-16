import { Phone, Mail, MapPin } from "lucide-react";
import Link from "next/link";

interface FooterLink {
  label: string;
  href: string;
}

interface FooterLinkGroup {
  title: string;
  items: FooterLink[];
}

interface FooterProps {
  businessName?: string;
  description?: string;
  phone?: string;
  email?: string;
  address?: string;
  links?: FooterLinkGroup[];
}

const DEFAULT_LINKS: FooterLinkGroup[] = [
  {
    title: "Company",
    items: [
      { label: "About", href: "/about" },
      { label: "Services", href: "/services" },
      { label: "Blog", href: "/blog" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    title: "Services",
    items: [
      { label: "Service One", href: "/services#one" },
      { label: "Service Two", href: "/services#two" },
      { label: "Service Three", href: "/services#three" },
    ],
  },
  {
    title: "Legal",
    items: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
    ],
  },
];

const DEFAULTS = {
  businessName: "Business Name",
  description:
    "A short description of the business and what makes it special. One to two sentences.",
  phone: "(555) 000-0000",
  email: "hello@example.com",
  address: "123 Main Street, City, ST 00000",
};

export function Footer(props: FooterProps) {
  const businessName = props.businessName ?? DEFAULTS.businessName;
  const description = props.description ?? DEFAULTS.description;
  const phone = props.phone ?? DEFAULTS.phone;
  const email = props.email ?? DEFAULTS.email;
  const address = props.address ?? DEFAULTS.address;
  const links = props.links ?? DEFAULT_LINKS;

  return (
    <footer className="bg-card border-t border-border">
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-16 md:py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 md:gap-8">
          {/* Brand Column */}
          <div className="lg:col-span-1">
            <Link href="/" className="text-xl font-heading font-bold">
              {businessName}
            </Link>
            <p className="mt-4 text-sm text-muted-foreground leading-relaxed max-w-xs">
              {description}
            </p>
            {/* Contact info */}
            <div className="mt-6 space-y-3">
              <a
                href={`tel:${phone.replace(/\D/g, "")}`}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Phone className="w-4 h-4 text-primary" />
                {phone}
              </a>
              <a
                href={`mailto:${email}`}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Mail className="w-4 h-4 text-primary" />
                {email}
              </a>
              <p className="flex items-start gap-2 text-sm text-muted-foreground">
                <MapPin className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                {address}
              </p>
            </div>
          </div>

          {/* Dynamic Link Groups */}
          {links.map((group) => (
            <div key={group.title}>
              <h4 className="font-heading font-semibold text-sm uppercase tracking-wider mb-4">
                {group.title}
              </h4>
              <ul className="space-y-3">
                {group.items.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-16 pt-8 border-t border-border flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} {businessName}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

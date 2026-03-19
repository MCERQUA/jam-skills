"use client";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Menu, X, Phone } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface NavItem {
  label: string;
  href: string;
}

interface NavCTA {
  label: string;
  href: string;
}

interface NavbarProps {
  logo?: string;
  navItems?: NavItem[];
  cta?: NavCTA;
  /**
   * Phone number for service businesses.
   * When provided, displays prominently on desktop (before the CTA button)
   * and in the mobile menu. Renders as a tel: link.
   * Standard pattern for local service sites — phone in header converts.
   */
  phone?: string;
}

const DEFAULT_NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "About", href: "/about" },
  { label: "Services", href: "/services" },
  { label: "Blog", href: "/blog" },
  { label: "Contact", href: "/contact" },
];

const DEFAULT_CTA: NavCTA = { label: "Get a Quote", href: "/contact" };

// REPLACE: Pass real business name via the logo prop.
const DEFAULTS = {
  logo: "REPLACE: Logo",
};

export function Navbar(props: NavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const logo = props.logo ?? DEFAULTS.logo;
  const navItems = props.navItems ?? DEFAULT_NAV_ITEMS;
  const cta = props.cta ?? DEFAULT_CTA;

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled
          ? "bg-background/90 backdrop-blur-lg border-b border-border shadow-sm"
          : "bg-background border-b border-border"
      )}
    >
      <nav className="max-w-7xl mx-auto px-4 md:px-6 h-16 md:h-20 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="text-xl font-heading font-bold text-foreground shrink-0">
          {logo}
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-6 lg:gap-8">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            >
              {item.label}
            </Link>
          ))}

          {/* Phone number — service business conversion driver */}
          {props.phone && (
            <a
              href={`tel:${props.phone.replace(/\D/g, "")}`}
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-primary/80 transition-colors"
              aria-label={`Call us at ${props.phone}`}
            >
              <Phone className="w-4 h-4" />
              {props.phone}
            </a>
          )}

          <Link
            href={cta.href}
            className="px-5 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 transition-colors cursor-pointer shrink-0"
          >
            {cta.label}
          </Link>
        </div>

        {/* Mobile: phone + hamburger */}
        <div className="md:hidden flex items-center gap-3">
          {props.phone && (
            <a
              href={`tel:${props.phone.replace(/\D/g, "")}`}
              className="inline-flex items-center gap-1 text-sm font-semibold text-primary"
              aria-label={`Call us at ${props.phone}`}
            >
              <Phone className="w-4 h-4" />
              <span className="hidden sm:inline">{props.phone}</span>
            </a>
          )}
          <button
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            className="p-2 cursor-pointer"
            aria-label={isMobileOpen ? "Close menu" : "Open menu"}
          >
            {isMobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-background border-b border-border overflow-hidden"
          >
            <div className="px-4 py-6 space-y-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileOpen(false)}
                  className="block text-lg font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  {item.label}
                </Link>
              ))}

              {/* Phone in mobile menu */}
              {props.phone && (
                <a
                  href={`tel:${props.phone.replace(/\D/g, "")}`}
                  className="flex items-center gap-2 text-lg font-bold text-primary py-1"
                  onClick={() => setIsMobileOpen(false)}
                >
                  <Phone className="w-5 h-5" />
                  {props.phone}
                </a>
              )}

              <Link
                href={cta.href}
                onClick={() => setIsMobileOpen(false)}
                className="block w-full text-center px-5 py-3 bg-primary text-primary-foreground font-semibold rounded-lg"
              >
                {cta.label}
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}

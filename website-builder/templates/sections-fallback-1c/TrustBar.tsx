"use client";
import { FadeIn } from "@/components/animations/FadeIn";
import { Shield, Award, Clock, Star, BadgeCheck, Headphones, Users, FileCheck, ClipboardList, FileText, type LucideIcon } from "lucide-react";

const iconMap: Record<string, LucideIcon> = {
  shield: Shield,
  award: Award,
  clock: Clock,
  star: Star,
  badgecheck: BadgeCheck,
  headphones: Headphones,
  users: Users,
  filecheck: FileCheck,
  clipboardlist: ClipboardList,
  filetext: FileText,
};

export interface TrustItem {
  icon?: string;
  label: string;
}

export interface TrustBarProps {
  items?: TrustItem[];
}

const defaultItems: TrustItem[] = [
  { icon: "shield", label: "Licensed Insurance Agency" },
  { icon: "award", label: "25+ Years Experience" },
  { icon: "clock", label: "24/7 Certificate Access" },
  { icon: "star", label: "Trusted by Contractors Nationwide" },
  { icon: "badgecheck", label: "Manufacturer Compliance" },
  { icon: "headphones", label: "Expert Support" },
];

export function TrustBar({ items = defaultItems }: TrustBarProps) {
  return (
    <section className="py-8 border-y border-border/50 bg-card/50">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        <FadeIn>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {items.map((item, i) => {
              const Icon = iconMap[item.icon?.toLowerCase() ?? ""] || Shield;
              return (
                <div key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Icon className="w-4 h-4 text-primary" />
                  <span className="font-medium whitespace-nowrap">{item.label}</span>
                </div>
              );
            })}
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

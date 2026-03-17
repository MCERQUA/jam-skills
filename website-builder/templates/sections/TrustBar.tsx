"use client";
import { FadeIn } from "@/components/animations/FadeIn";
import { Shield, Award, Clock, Star, BadgeCheck, Headphones, type LucideIcon } from "lucide-react";

export interface TrustItem {
  icon?: LucideIcon;
  label: string;
}

export interface TrustBarProps {
  items?: TrustItem[];
}

// REPLACE: Pass real trust signals via the items prop.
const defaultItems: TrustItem[] = [
  { icon: Shield, label: "REPLACE: Trust Signal 1" },
  { icon: Award, label: "REPLACE: Trust Signal 2" },
  { icon: Clock, label: "REPLACE: Trust Signal 3" },
  { icon: Star, label: "REPLACE: Trust Signal 4" },
  { icon: BadgeCheck, label: "REPLACE: Trust Signal 5" },
  { icon: Headphones, label: "REPLACE: Trust Signal 6" },
];

export function TrustBar({ items = defaultItems }: TrustBarProps) {
  return (
    <section className="py-8 border-y border-border/50 bg-card/50">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        <FadeIn>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {items.map((item, i) => {
              const Icon = item.icon || Shield;
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

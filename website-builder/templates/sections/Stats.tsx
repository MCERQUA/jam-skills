"use client";
import { FadeIn } from "@/components/animations/FadeIn";
import { Counter } from "@/components/animations/Counter";

interface StatItem {
  value: number;
  suffix?: string;
  label: string;
}

interface StatsProps {
  stats?: StatItem[];
}

const DEFAULT_STATS: StatItem[] = [
  { value: 500, suffix: "+", label: "Happy Clients" },
  { value: 15, suffix: "+", label: "Years Experience" },
  { value: 98, suffix: "%", label: "Satisfaction Rate" },
  { value: 24, suffix: "/7", label: "Support Available" },
];

export function Stats(props: StatsProps) {
  const stats = props.stats ?? DEFAULT_STATS;

  return (
    <section className="py-20 md:py-28">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          {stats.map((stat, i) => (
            <FadeIn key={i} delay={i * 0.1} className="text-center">
              <div className="text-4xl md:text-5xl font-heading font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                <Counter target={stat.value} suffix={stat.suffix} />
              </div>
              <p className="mt-2 text-sm md:text-base text-muted-foreground font-medium">
                {stat.label}
              </p>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

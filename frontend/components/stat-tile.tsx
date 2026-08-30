import type { Icon } from "@phosphor-icons/react";

import { cn } from "@/lib/utils";

interface StatTileProps {
  label: React.ReactNode;
  value: React.ReactNode;
  icon?: Icon;
  delta?: React.ReactNode;
  deltaTone?: "positive" | "negative" | "neutral";
  className?: string;
}

const DELTA_STYLES: Record<NonNullable<StatTileProps["deltaTone"]>, string> = {
  positive: "text-status-success",
  negative: "text-status-danger",
  neutral: "text-muted-foreground",
};

export function StatTile({ label, value, icon: IconComponent, delta, deltaTone = "neutral", className }: StatTileProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1.5 rounded-xl bg-card p-4 shadow-card ring-1 ring-foreground/10",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        {IconComponent ? <IconComponent className="size-4 text-primary" /> : null}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-display text-2xl font-semibold text-foreground">{value}</span>
        {delta ? <span className={cn("text-xs font-medium", DELTA_STYLES[deltaTone])}>{delta}</span> : null}
      </div>
    </div>
  );
}

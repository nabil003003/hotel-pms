"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { DAY_WIDTH, ROW_HEIGHT } from "./geometry";
import type { Booking } from "@/lib/api-clients/reservation";
import { cn } from "@/lib/utils";
import { User, Moon, DotsSixVertical } from "@phosphor-icons/react";

const STATUS_BAR_STYLES: Record<string, string> = {
  status_confirmed: "bg-sky-600 border-sky-700 text-white hover:bg-sky-700",
  status_checked_in: "bg-emerald-600 border-emerald-700 text-white hover:bg-emerald-700",
  status_option: "bg-amber-500 border-amber-600 text-amber-950 hover:bg-amber-600",
  status_voucher: "bg-indigo-600 border-indigo-700 text-white hover:bg-indigo-700",
  status_checked_out: "bg-slate-400 border-slate-500 text-white opacity-80",
  status_cancelled: "bg-rose-400 border-rose-500 text-white line-through opacity-60",
  status_no_show: "bg-purple-700 border-purple-800 text-white opacity-70",
};

const STATUS_LABELS: Record<string, string> = {
  status_confirmed: "Confirmée",
  status_checked_in: "En séjour",
  status_option: "Option",
  status_voucher: "Voucher",
  status_checked_out: "Terminée",
  status_cancelled: "Annulée",
  status_no_show: "No-show",
};

interface PlanningBarProps {
  booking: Booking;
  customerName?: string;
  geom: { startIdx: number; nightCount: number };
  isDraggable?: boolean;
  onClick?: () => void;
  isOverlay?: boolean;
}

export function PlanningBar({
  booking,
  customerName,
  geom,
  isDraggable = true,
  onClick,
  isOverlay = false,
}: PlanningBarProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: booking.id,
    data: { booking },
    disabled: !isDraggable || isOverlay,
  });

  const style: React.CSSProperties = isOverlay
    ? {
        width: `${geom.nightCount * DAY_WIDTH - 4}px`,
        height: `${ROW_HEIGHT - 12}px`,
      }
    : {
        position: "absolute",
        left: `${geom.startIdx * DAY_WIDTH + 2}px`,
        width: `${geom.nightCount * DAY_WIDTH - 4}px`,
        height: `${ROW_HEIGHT - 12}px`,
        top: "6px",
        transform: CSS.Translate.toString(transform),
      };

  const statusStyle = STATUS_BAR_STYLES[booking.status] ?? "bg-primary text-primary-foreground";
  const nameLabel = customerName || "Client inconnu";

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...(isDraggable && !isOverlay ? { ...attributes, ...listeners } : {})}
      onClick={(e) => {
        if (!isDragging && onClick) {
          e.stopPropagation();
          onClick();
        }
      }}
      className={cn(
        "group relative flex items-center gap-1.5 rounded-lg border px-2 text-xs font-medium shadow-sm transition-all select-none z-10",
        statusStyle,
        isDraggable && !isOverlay && "cursor-grab active:cursor-grabbing",
        isDragging && "opacity-30 border-dashed",
        isOverlay && "cursor-grabbing shadow-xl ring-2 ring-primary z-50 opacity-95 scale-[1.02]"
      )}
      title={`${nameLabel} — ${STATUS_LABELS[booking.status] || booking.status} (${geom.nightCount} nuit(s))`}
    >
      {isDraggable && !isOverlay && (
        <DotsSixVertical className="w-3.5 h-3.5 flex-shrink-0 opacity-60 group-hover:opacity-100" />
      )}
      <User className="w-3.5 h-3.5 flex-shrink-0 opacity-90" />
      <span className="truncate font-semibold">{nameLabel}</span>
      <span className="ml-auto hidden sm:flex items-center gap-0.5 text-[10px] opacity-90 flex-shrink-0 font-normal">
        <Moon className="w-3 h-3" />
        {geom.nightCount}n
      </span>
    </div>
  );
}

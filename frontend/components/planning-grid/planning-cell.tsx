"use client";

import { useDroppable } from "@dnd-kit/core";
import { DAY_WIDTH, ROW_HEIGHT } from "./geometry";
import { cn } from "@/lib/utils";

interface PlanningCellProps {
  roomId: string;
  dateIso: string;
  isToday?: boolean;
}

export function PlanningCell({ roomId, dateIso, isToday }: PlanningCellProps) {
  const cellId = `${roomId}__${dateIso}`;
  const { isOver, setNodeRef } = useDroppable({
    id: cellId,
    data: {
      roomId,
      dateIso,
    },
  });

  return (
    <div
      ref={setNodeRef}
      style={{
        width: `${DAY_WIDTH}px`,
        height: `${ROW_HEIGHT}px`,
      }}
      className={cn(
        "box-border flex-shrink-0 border-b border-r border-border/40 transition-colors",
        isToday && "bg-muted/30",
        isOver ? "bg-primary/20 border-primary" : "hover:bg-accent/20"
      )}
    />
  );
}

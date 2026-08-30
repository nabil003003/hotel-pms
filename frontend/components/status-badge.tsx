import { cn } from "@/lib/utils";

const ROOM_STATUS_STYLES: Record<string, string> = {
  Sale: "bg-status-neutral/10 text-status-neutral",
  Nettoyage: "bg-status-warning/10 text-status-warning",
  Propre: "bg-status-success/10 text-status-success",
  Contrôlée: "bg-status-info/10 text-status-info",
  Bloquée: "bg-status-danger/10 text-status-danger",
};

export function RoomStatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        ROOM_STATUS_STYLES[status] ?? "bg-muted text-muted-foreground"
      )}
    >
      {status}
    </span>
  );
}

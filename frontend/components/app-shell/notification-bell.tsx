"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Bell } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  fetchMyNotifications,
  markNotificationRead,
  STAFF_ROLE_LABELS,
  type Notification,
} from "@/lib/api-clients/notification";
import { useSessionStore } from "@/store/session-store";

// 20s : assez réactif pour "voir un message arriver sans recharger la page"
// sans bombarder notification-service — pas de WebSocket dans ce sprint (D11).
const POLL_INTERVAL_MS = 20_000;

export function NotificationBell() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const queryClient = useQueryClient();

  const { data: notifications } = useQuery({
    queryKey: ["my-notifications", establishmentId],
    queryFn: () => fetchMyNotifications(establishmentId as string),
    enabled: Boolean(establishmentId),
    refetchInterval: POLL_INTERVAL_MS,
  });

  const readMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  if (!establishmentId) return null;

  const items = notifications ?? [];
  const unreadCount = items.filter((n) => !n.read_at).length;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -right-1 -top-1 h-4 min-w-4 justify-center rounded-full px-1 text-[10px] leading-none"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <div className="flex items-center justify-between border-b border-border px-3 py-2">
          <span className="text-sm font-semibold">Notifications</span>
          {unreadCount > 0 && <span className="text-xs text-muted-foreground">{unreadCount} non lue{unreadCount > 1 ? "s" : ""}</span>}
        </div>
        <div className="max-h-96 overflow-y-auto">
          {items.length === 0 ? (
            <p className="p-4 text-center text-xs text-muted-foreground">Rien pour le moment.</p>
          ) : (
            items.slice(0, 10).map((n: Notification) => (
              <button
                key={n.id}
                type="button"
                onClick={() => !n.read_at && readMutation.mutate(n.id)}
                className="flex w-full flex-col gap-0.5 border-b border-border px-3 py-2 text-left last:border-b-0 hover:bg-muted/50"
              >
                <span className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                  {!n.read_at && <span className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-status-info" />}
                  {n.subject}
                </span>
                <span className="line-clamp-2 text-xs text-muted-foreground">{n.body}</span>
                <span className="text-[10px] text-muted-foreground">
                  {STAFF_ROLE_LABELS[n.recipient_role] ?? n.recipient_role} · {new Date(n.created_at).toLocaleString("fr-FR")}
                </span>
              </button>
            ))
          )}
        </div>
        <Link
          href="/notifications"
          className="block border-t border-border px-3 py-2 text-center text-xs font-medium text-foreground hover:bg-muted/50"
        >
          Voir toutes les notifications
        </Link>
      </PopoverContent>
    </Popover>
  );
}

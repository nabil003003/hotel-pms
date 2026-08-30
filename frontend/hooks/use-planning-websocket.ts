import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

const RESERVATION_WS_BASE =
  process.env.NEXT_PUBLIC_RESERVATION_WS_URL ?? "ws://localhost:8007";

/**
 * Relai temps réel pour le planning réservations — se connecte à
 * /ws/planning de reservation-service et invalide le cache React Query des
 * réservations à chaque message (Redis pub/sub `booking_updated`).
 */
export function usePlanningWebSocket(establishmentId: string | null) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!establishmentId) return;

    let socket: WebSocket | null = null;
    let cancelled = false;

    async function connect() {
      const tokenRes = await fetch("/api/auth/ws-token");
      if (!tokenRes.ok || cancelled) return;
      const { token } = await tokenRes.json();

      const url = `${RESERVATION_WS_BASE}/api/v1/ws/planning?establishment_id=${establishmentId}&token=${token}`;
      socket = new WebSocket(url);

      socket.onmessage = () => {
        queryClient.invalidateQueries({ queryKey: ["bookings", establishmentId] });
      };
    }

    connect();

    return () => {
      cancelled = true;
      socket?.close();
    };
  }, [establishmentId, queryClient]);
}

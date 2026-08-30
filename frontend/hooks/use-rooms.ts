import { useQuery } from "@tanstack/react-query";

import { fetchRooms } from "@/lib/api-clients/housekeeping";

export function useRooms(establishmentId: string | null) {
  return useQuery({
    queryKey: ["rooms", establishmentId],
    queryFn: () => fetchRooms(establishmentId as string),
    enabled: Boolean(establishmentId),
  });
}

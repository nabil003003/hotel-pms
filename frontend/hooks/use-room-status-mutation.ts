import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { changeRoomStatus } from "@/lib/api-clients/housekeeping";

export function useRoomStatusMutation(establishmentId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      roomId,
      newStatus,
      reason,
    }: {
      roomId: string;
      newStatus: string;
      reason?: string;
    }) => changeRoomStatus(roomId, newStatus, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms", establishmentId] });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

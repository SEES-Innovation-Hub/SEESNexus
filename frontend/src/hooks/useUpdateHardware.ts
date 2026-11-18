import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateHardware } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";
import type { HardwarePayload } from "../types/hardware";

// Used for edits and for putting a retired item back in service.
export function useUpdateHardware() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<HardwarePayload> }) => updateHardware(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.hardware.lists });
      // Loans carry the item's name, so a rename shows up there too.
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.loans });
      void queryClient.invalidateQueries({ queryKey: queryKeys.loans.mine });
    },
  });
}

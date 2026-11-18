import { useMutation, useQueryClient } from "@tanstack/react-query";
import { retireHardware } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";

export function useRetireHardware() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: retireHardware,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.hardware.lists });
      // Loans carry the item's name, so a rename shows up there too.
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.loans });
      void queryClient.invalidateQueries({ queryKey: queryKeys.loans.mine });
    },
  });
}

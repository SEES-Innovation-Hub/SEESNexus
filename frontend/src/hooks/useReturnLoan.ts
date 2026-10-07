import { useMutation, useQueryClient } from "@tanstack/react-query";
import { returnLoan } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";

// Returning puts a unit back on the shelf, so the hardware lists refresh too.
export function useReturnLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: returnLoan,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.loans.mine });
      void queryClient.invalidateQueries({ queryKey: queryKeys.hardware.lists });
    },
  });
}

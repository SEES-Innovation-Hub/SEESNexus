import { useMutation, useQueryClient } from "@tanstack/react-query";
import { returnLoan } from "../api/admin";
import { queryKeys } from "../api/queryKeys";

// Admin only. A returned unit goes back on the shelf, so availability changes too.
export function useReturnLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: returnLoan,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.loans });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
      void queryClient.invalidateQueries({ queryKey: queryKeys.hardware.lists });
      void queryClient.invalidateQueries({ queryKey: queryKeys.loans.mine });
    },
  });
}

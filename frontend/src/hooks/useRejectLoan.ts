import { useMutation, useQueryClient } from "@tanstack/react-query";
import { rejectLoan } from "../api/admin";
import { queryKeys } from "../api/queryKeys";

// A rejected request never held a unit, so hardware availability is unchanged.
export function useRejectLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: rejectLoan,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.loans });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cancelLoanRequest } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";

// A pending request never held a unit, so only the loan lists change.
export function useCancelLoanRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: cancelLoanRequest,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.loans.mine });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.loans });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

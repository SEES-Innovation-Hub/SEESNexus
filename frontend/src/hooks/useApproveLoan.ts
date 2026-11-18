import { useMutation, useQueryClient } from "@tanstack/react-query";
import { approveLoan } from "../api/admin";
import { queryKeys } from "../api/queryKeys";

// Approving takes a unit off the shelf, so the loan lists, the stats and the
// hardware availability all change.
export function useApproveLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: approveLoan,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.loans });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
      void queryClient.invalidateQueries({ queryKey: queryKeys.hardware.lists });
    },
  });
}

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { requestLoan } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";
import type { Loan, LoanRequestPayload } from "../types/hardware";

// A request doesn't move any units (only an admin's approval does), so only
// My Loans changes. The server returns the new loan, which is added to the
// cached list at once so the hardware card shows "Requested" immediately.
export function useRequestLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ hardwareId, payload }: { hardwareId: string; payload: LoanRequestPayload }) =>
      requestLoan(hardwareId, payload),
    onSuccess: (loan) => {
      queryClient.setQueryData<Loan[]>(queryKeys.loans.mine, (loans) => [loan, ...(loans ?? [])]);
    },
  });
}

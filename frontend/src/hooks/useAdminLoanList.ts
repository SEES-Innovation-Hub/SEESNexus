import type { User } from "../types/auth";
import { useAdminLoans } from "./useAdminLoans";
import { useAdminUsers } from "./useAdminUsers";
import { useHardwareNames } from "./useHardwareNames";

// Loans carry only ids, so the admin pages join them with the user list (for
// the borrower) and the hardware lookups (for the item name).
export function useAdminLoanList() {
  const loansQuery = useAdminLoans();
  const { data: users } = useAdminUsers();
  const loans = loansQuery.data ?? [];
  const itemNames = useHardwareNames(loans.map((loan) => loan.hardware_id));
  const borrowers = new Map<string, User>((users ?? []).map((user) => [user.id, user]));

  return {
    loans: loansQuery.data,
    isPending: loansQuery.isPending,
    isError: loansQuery.isError,
    isFetching: loansQuery.isFetching,
    refetch: loansQuery.refetch,
    itemNames,
    borrowers,
  };
}

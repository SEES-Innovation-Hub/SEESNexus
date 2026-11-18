import type { User } from "../types/auth";
import { useAdminLoans } from "./useAdminLoans";
import { useAdminUsers } from "./useAdminUsers";

// Loans carry the borrower's id only, so the admin pages join them with the
// user list. (The item's name comes with each loan.)
export function useAdminLoanList() {
  const loansQuery = useAdminLoans();
  const { data: users } = useAdminUsers();
  const borrowers = new Map<string, User>((users ?? []).map((user) => [user.id, user]));

  return {
    loans: loansQuery.data,
    isPending: loansQuery.isPending,
    isError: loansQuery.isError,
    isFetching: loansQuery.isFetching,
    refetch: loansQuery.refetch,
    borrowers,
  };
}

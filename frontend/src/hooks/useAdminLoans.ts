import { useQuery } from "@tanstack/react-query";
import { listAllLoans } from "../api/admin";
import { queryKeys } from "../api/queryKeys";

// Every member's loans, for the admin pages.
export function useAdminLoans() {
  return useQuery({ queryKey: queryKeys.admin.loans, queryFn: listAllLoans });
}

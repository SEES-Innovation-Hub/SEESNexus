import { useQuery } from "@tanstack/react-query";
import { listUsers } from "../api/admin";
import { queryKeys } from "../api/queryKeys";

// Every account. Also how the loan pages show who a borrower is, since a loan
// only carries borrower_id.
export function useAdminUsers() {
  return useQuery({ queryKey: queryKeys.admin.users, queryFn: listUsers });
}

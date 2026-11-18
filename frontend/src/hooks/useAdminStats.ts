import { useQuery } from "@tanstack/react-query";
import { getAdminStats } from "../api/admin";
import { queryKeys } from "../api/queryKeys";

// The real counts behind the admin overview (no hardcoded numbers: v1's bug).
export function useAdminStats() {
  return useQuery({ queryKey: queryKeys.admin.stats, queryFn: getAdminStats });
}

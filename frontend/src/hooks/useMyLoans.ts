import { useQuery } from "@tanstack/react-query";
import { listMyLoans } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";
import { useAuth } from "./useAuth";

// The signed-in person's loans. Visitors have none, so nothing is requested.
export function useMyLoans() {
  const { user } = useAuth();
  return useQuery({
    queryKey: queryKeys.loans.mine,
    queryFn: listMyLoans,
    enabled: user !== null,
  });
}

import { useQueries } from "@tanstack/react-query";
import { getHardware } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";

const ONE_HOUR = 60 * 60 * 1000;

// Loans only carry hardware_id, so My Loans looks up each borrowed item's name
// (one cached request per distinct item; names rarely change, hence an hour).
// Remove this once the backend includes the name in the loan response.
export function useHardwareNames(hardwareIds: string[]): Record<string, string | undefined> {
  const ids = [...new Set(hardwareIds)];
  const results = useQueries({
    queries: ids.map((id) => ({
      queryKey: queryKeys.hardware.detail(id),
      queryFn: () => getHardware(id),
      staleTime: ONE_HOUR,
    })),
  });
  return Object.fromEntries(ids.map((id, index) => [id, results[index].data?.name]));
}

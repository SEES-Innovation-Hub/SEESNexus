import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { listHardware, type HardwareListParams } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";

// One page of hardware. The previous page stays on screen while the next loads.
export function useHardwareList(params: HardwareListParams) {
  return useQuery({
    queryKey: queryKeys.hardware.list(params),
    queryFn: () => listHardware(params),
    placeholderData: keepPreviousData,
  });
}

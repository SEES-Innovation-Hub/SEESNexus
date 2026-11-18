import { useMutation, useQueryClient } from "@tanstack/react-query";
import { retireHardware } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";

export function useRetireHardware() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: retireHardware,
    onSuccess: (item) => {
      queryClient.setQueryData(queryKeys.hardware.detail(item.id), item);
      void queryClient.invalidateQueries({ queryKey: queryKeys.hardware.lists });
    },
  });
}

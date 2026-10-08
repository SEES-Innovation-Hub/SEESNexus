import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createHardware } from "../api/hardware";
import { queryKeys } from "../api/queryKeys";

export function useCreateHardware() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createHardware,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.hardware.lists });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

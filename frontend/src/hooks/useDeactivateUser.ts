import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deactivateUser } from "../api/admin";
import { queryKeys } from "../api/queryKeys";

export function useDeactivateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.users });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

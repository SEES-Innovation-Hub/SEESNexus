import { useMutation, useQueryClient } from "@tanstack/react-query";
import { activateUser, deactivateUser } from "../api/admin";
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

export function useActivateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: activateUser,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.users });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { changeUserRole } from "../api/admin";
import { queryKeys } from "../api/queryKeys";
import type { UserRole } from "../types/auth";

// The role counts on the admin overview change too.
export function useChangeUserRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role, adminKey }: { userId: string; role: UserRole; adminKey?: string }) =>
      changeUserRole(userId, role, adminKey),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.users });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

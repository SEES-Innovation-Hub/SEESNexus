import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  cancelRegistration,
  createEvent,
  deleteEvent,
  registerForEvent,
  restoreEvent,
  setAttendance,
  updateEvent,
} from "../api/events";
import { queryKeys } from "../api/queryKeys";
import type { EventPayload } from "../types/events";

// Changes to events. Almost every one moves a count that several screens show
// (places left on the list, the detail page, My events, the participant list),
// so each refreshes everything under ["events"]; it is a handful of small reads.
function useEventMutation<TVariables, TResult>(
  mutationFn: (variables: TVariables) => Promise<TResult>,
  { affectsStats = false } = {},
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.events.all });
      if (affectsStats) void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

export const useRegisterForEvent = () => useEventMutation(registerForEvent);
export const useCancelRegistration = () => useEventMutation(cancelRegistration);

export const useCreateEvent = () => useEventMutation(createEvent, { affectsStats: true });
export const useUpdateEvent = () =>
  useEventMutation(({ id, payload }: { id: string; payload: Partial<EventPayload> }) => updateEvent(id, payload));
export const useDeleteEvent = () => useEventMutation(deleteEvent, { affectsStats: true });
export const useRestoreEvent = () => useEventMutation(restoreEvent, { affectsStats: true });

export const useSetAttendance = () =>
  useEventMutation(
    ({ eventId, registrationId, attended }: { eventId: string; registrationId: string; attended: boolean }) =>
      setAttendance(eventId, registrationId, attended),
  );

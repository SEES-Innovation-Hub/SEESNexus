import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  cancelRegistration,
  checkIn,
  closeCheckIn,
  openCheckIn,
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
    // Returned, so the action only counts as finished once the screens show the
    // new state: no flicker back to the old value between "saved" and "refreshed".
    onSuccess: () => {
      if (affectsStats) void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
      return queryClient.invalidateQueries({ queryKey: queryKeys.events.all });
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

export const useCheckIn = () =>
  useEventMutation(({ eventId, code }: { eventId: string; code: string }) => checkIn(eventId, code));
export const useOpenCheckIn = () => useEventMutation(openCheckIn);
export const useCloseCheckIn = () => useEventMutation(closeCheckIn);

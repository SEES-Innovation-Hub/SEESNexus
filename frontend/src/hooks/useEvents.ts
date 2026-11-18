import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  getEvent,
  listEvents,
  listMyRegistrations,
  listParticipants,
  type EventListParams,
} from "../api/events";
import { queryKeys } from "../api/queryKeys";
import { useAuth } from "./useAuth";

// Reads for the Events pages. Each is its own small hook, kept in one file
// because they share the same keys and are always used together.

// One page of events. Previous results stay on screen while the next loads.
export function useEventList(params: EventListParams) {
  return useQuery({
    queryKey: queryKeys.events.list(params),
    queryFn: () => listEvents(params),
    placeholderData: keepPreviousData,
  });
}

export function useEvent(id: string) {
  return useQuery({ queryKey: queryKeys.events.detail(id), queryFn: () => getEvent(id) });
}

// The signed-in member's registrations. Event pages use it to know whether to
// show "Register" or "Cancel", so it is cheap to call from several places.
export function useMyRegistrations() {
  const { user } = useAuth();
  return useQuery({
    queryKey: queryKeys.events.mine,
    queryFn: listMyRegistrations,
    enabled: user !== null,
  });
}

// Admin only.
export function useParticipants(eventId: string) {
  return useQuery({
    queryKey: queryKeys.events.participants(eventId),
    queryFn: () => listParticipants(eventId),
  });
}

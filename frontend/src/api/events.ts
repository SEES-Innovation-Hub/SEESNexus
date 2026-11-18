import { api, unwrap } from "./client";
import type {
  EventPayload,
  EventType,
  MyRegistration,
  PaginatedEvents,
  Participant,
  Registration,
  SeesEvent,
} from "../types/events";

// Every route needs a login (backend/app/api/v1/events.py).

export interface EventListParams {
  page?: number;
  pageSize?: number;
  eventType?: EventType;
  // Only events that haven't started yet.
  upcoming?: boolean;
  // Admin only: soft-deleted events instead of live ones.
  deleted?: boolean;
}

// Soonest first.
export function listEvents({ page, pageSize, eventType, upcoming, deleted }: EventListParams = {}) {
  return unwrap<PaginatedEvents>(
    api.get("/events", {
      params: {
        page,
        page_size: pageSize,
        event_type: eventType,
        upcoming: upcoming || undefined,
        deleted: deleted || undefined,
      },
    }),
  );
}

export function getEvent(id: string) {
  return unwrap<SeesEvent>(api.get(`/events/${id}`));
}

// Confirmed while places last, then waitlisted. Refused after the deadline.
export function registerForEvent(id: string) {
  return unwrap<Registration>(api.post(`/events/${id}/register`));
}

// Allowed until the event starts. A freed place goes to the first person waiting.
export function cancelRegistration(id: string) {
  return unwrap<Registration>(api.delete(`/events/${id}/register`));
}

// Every event the signed-in member registered for, in any state, newest first.
export function listMyRegistrations() {
  return unwrap<MyRegistration[]>(api.get("/events/registrations/my"));
}

// --- admin ---

export function createEvent(payload: EventPayload) {
  return unwrap<SeesEvent>(api.post("/events", payload));
}

// Lowering max_participants below the confirmed count is refused (400);
// raising it moves people off the waitlist.
export function updateEvent(id: string, payload: Partial<EventPayload>) {
  return unwrap<SeesEvent>(api.put(`/events/${id}`, payload));
}

// Soft delete; restoreEvent brings it back with its registrations.
export function deleteEvent(id: string) {
  return unwrap<null>(api.delete(`/events/${id}`));
}

export function restoreEvent(id: string) {
  return unwrap<SeesEvent>(api.post(`/events/${id}/restore`));
}

// Oldest registration first.
export function listParticipants(id: string) {
  return unwrap<Participant[]>(api.get(`/events/${id}/participants`));
}

// Only a CONFIRMED registration can be marked.
export function setAttendance(eventId: string, registrationId: string, attended: boolean) {
  return unwrap<Registration>(
    api.put(`/events/${eventId}/participants/${registrationId}/attendance`, { attended }),
  );
}

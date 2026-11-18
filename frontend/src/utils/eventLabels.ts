import type { BadgeTone } from "../components/Badge";
import type { EventType, RegistrationStatus, SeesEvent } from "../types/events";
import { parseApiDate } from "./parseApiDate";

export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  HACKATHON: "Hackathon",
  WORKSHOP: "Workshop",
  SEMINAR: "Seminar",
  CONFERENCE: "Conference",
  ORIENTATION: "Orientation",
};

export const EVENT_TYPE_OPTIONS = Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => ({
  value: value as EventType,
  label,
}));

export const REGISTRATION_STATUS_LABELS: Record<RegistrationStatus, string> = {
  CONFIRMED: "You're going",
  WAITLISTED: "On the waitlist",
  CANCELLED: "Cancelled",
};

export const REGISTRATION_STATUS_TONES: Record<RegistrationStatus, BadgeTone> = {
  CONFIRMED: "mint",
  WAITLISTED: "mustard",
  CANCELLED: "neutral",
};

export function isEventType(value: string | null): value is EventType {
  return value !== null && Object.hasOwn(EVENT_TYPE_LABELS, value);
}

// "Sat 14 Nov 2026, 10:00 to 16:00", or both dates when it runs over midnight.
export function eventWhen(event: Pick<SeesEvent, "start_date" | "end_date">): string {
  const start = parseApiDate(event.start_date);
  const end = parseApiDate(event.end_date);
  const day = (d: Date) => d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
  const time = (d: Date) => d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  return start.toDateString() === end.toDateString()
    ? `${day(start)}, ${time(start)} to ${time(end)}`
    : `${day(start)}, ${time(start)} to ${day(end)}, ${time(end)}`;
}

export function formatDateTime(value: string): string {
  return parseApiDate(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function hasStarted(event: Pick<SeesEvent, "start_date">, now = Date.now()): boolean {
  return parseApiDate(event.start_date).getTime() <= now;
}

// Members can check in from an hour before the start until the end (the
// backend applies the same window).
const CHECKIN_OPENS_BEFORE_MS = 60 * 60 * 1000;
export function inCheckInWindow(event: Pick<SeesEvent, "start_date" | "end_date">, now = Date.now()): boolean {
  return (
    now >= parseApiDate(event.start_date).getTime() - CHECKIN_OPENS_BEFORE_MS &&
    now <= parseApiDate(event.end_date).getTime()
  );
}

export function registrationClosed(event: Pick<SeesEvent, "registration_deadline">, now = Date.now()): boolean {
  return parseApiDate(event.registration_deadline).getTime() < now;
}

// "3 places left", "Full", "No limit".
export function placesSummary(event: SeesEvent): string {
  if (event.spots_left === null) return `${event.confirmed_count} going · no limit`;
  if (event.spots_left === 0) return `Full · ${event.confirmed_count} going`;
  return `${event.spots_left} of ${event.max_participants} places left`;
}

import type { EventPayload, EventType, SeesEvent } from "../../types/events";
import { isHttpUrl } from "../../utils/isHttpUrl";

// What the form edits. Date inputs (datetime-local) hold "YYYY-MM-DDTHH:mm" in
// the admin's own timezone; toPayload turns them into full ISO timestamps.
export interface EventFormValues {
  title: string;
  description: string;
  eventType: EventType | "";
  location: string;
  isVirtual: boolean;
  virtualLink: string;
  bannerUrl: string;
  startDate: string;
  endDate: string;
  registrationDeadline: string;
  // "" = no limit.
  maxParticipants: string;
}

export type EventFormErrors = Partial<Record<keyof EventFormValues, string>>;

// Limits match backend/app/schemas/events.py.
export const TITLE_MAX = 255;
export const LOCATION_MAX = 500;
export const URL_MAX = 500;

export const EMPTY_VALUES: EventFormValues = {
  title: "",
  description: "",
  eventType: "",
  location: "",
  isVirtual: false,
  virtualLink: "",
  bannerUrl: "",
  startDate: "",
  endDate: "",
  registrationDeadline: "",
  maxParticipants: "",
};

// ISO timestamp -> the local "YYYY-MM-DDTHH:mm" a datetime-local input shows.
export function toLocalInput(iso: string): string {
  const date = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function toFormValues(event: SeesEvent): EventFormValues {
  return {
    title: event.title,
    description: event.description,
    eventType: event.event_type,
    location: event.location,
    isVirtual: event.is_virtual,
    virtualLink: event.virtual_link ?? "",
    bannerUrl: event.banner_url ?? "",
    startDate: toLocalInput(event.start_date),
    endDate: toLocalInput(event.end_date),
    registrationDeadline: toLocalInput(event.registration_deadline),
    maxParticipants: event.max_participants === null ? "" : String(event.max_participants),
  };
}

function validateUrl(value: string, required: boolean): string | undefined {
  if (value === "") return required ? "Add the meeting link." : undefined;
  if (!isHttpUrl(value)) return "Enter a full link starting with https://";
  if (value.length > URL_MAX) return `Keep the link under ${URL_MAX} characters.`;
  return undefined;
}

// confirmedCount: when editing, the cap can't drop below the people already going.
export function validate(values: EventFormValues, confirmedCount = 0): EventFormErrors {
  const start = Date.parse(values.startDate);
  const end = Date.parse(values.endDate);
  const deadline = Date.parse(values.registrationDeadline);
  const max = values.maxParticipants.trim();

  let maxError: string | undefined;
  if (max !== "") {
    const n = Number(max);
    if (!Number.isInteger(n) || n < 1) maxError = "Enter a whole number of 1 or more, or leave it empty for no limit.";
    else if (n < confirmedCount) maxError = `${confirmedCount} people already have a place, so the limit can't go below that.`;
  }

  const errors: EventFormErrors = {
    title: values.title.trim() ? undefined : "Give the event a title.",
    description: values.description.trim() ? undefined : "Say what the event is about.",
    eventType: values.eventType ? undefined : "Pick a type.",
    location: values.location.trim() ? undefined : values.isVirtual ? 'Say where, e.g. "Online".' : "Say where it happens.",
    startDate: Number.isNaN(start) ? "Choose when it starts." : undefined,
    endDate: Number.isNaN(end) ? "Choose when it ends." : !Number.isNaN(start) && end <= start ? "It has to end after it starts." : undefined,
    registrationDeadline: Number.isNaN(deadline)
      ? "Choose when registration closes."
      : !Number.isNaN(start) && deadline > start
        ? "Registration has to close by the time the event starts."
        : undefined,
    maxParticipants: maxError,
    virtualLink: values.isVirtual ? validateUrl(values.virtualLink.trim(), true) : undefined,
    bannerUrl: validateUrl(values.bannerUrl.trim(), false),
  };
  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message)) as EventFormErrors;
}

// Only call after validate() returned no errors.
export function toPayload(values: EventFormValues): EventPayload {
  const max = values.maxParticipants.trim();
  return {
    title: values.title.trim(),
    description: values.description.trim(),
    event_type: values.eventType as EventType,
    location: values.location.trim(),
    is_virtual: values.isVirtual,
    // The backend refuses a link on an in-person event.
    virtual_link: values.isVirtual ? values.virtualLink.trim() : null,
    banner_url: values.bannerUrl.trim() || null,
    start_date: new Date(values.startDate).toISOString(),
    end_date: new Date(values.endDate).toISOString(),
    registration_deadline: new Date(values.registrationDeadline).toISOString(),
    max_participants: max === "" ? null : Number(max),
  };
}

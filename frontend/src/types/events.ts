// Mirrors backend/app/schemas/events.py and models/events.py — keep in sync.
export type EventType = "HACKATHON" | "WORKSHOP" | "SEMINAR" | "CONFERENCE" | "ORIENTATION";
export type RegistrationStatus = "CONFIRMED" | "WAITLISTED" | "CANCELLED";

// Dates are ISO strings with a timezone.
export interface SeesEvent {
  id: string;
  title: string;
  description: string;
  event_type: EventType;
  location: string;
  is_virtual: boolean;
  // Only sent to admins and to students with a confirmed place; null otherwise.
  virtual_link: string | null;
  banner_url: string | null;
  start_date: string;
  end_date: string;
  registration_deadline: string;
  // null = no limit.
  max_participants: number | null;
  created_by_id: string;
  created_at: string;
  // Only ever set when an admin looks at a deleted event.
  deleted_at: string | null;
  confirmed_count: number;
  attended_count: number;
  // Self check-in is open. The code itself is only sent to admins.
  checkin_open: boolean;
  checkin_code: string | null;
  // null when there is no limit.
  spots_left: number | null;
}

export interface PaginatedEvents {
  items: SeesEvent[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface Registration {
  id: string;
  event_id: string;
  student_id: string;
  status: RegistrationStatus;
  registered_at: string;
  attended_at: string | null;
}

// GET /events/registrations/my
export interface MyRegistration extends Registration {
  // 1 = next in line; null unless WAITLISTED.
  waitlist_position: number | null;
  event_deleted: boolean;
  event: SeesEvent;
}

// GET /events/:id/participants (admin)
export interface Participant extends Registration {
  student_name: string;
  student_email: string;
}

// POST /events and PUT /events/:id (admin).
export interface EventPayload {
  title: string;
  description: string;
  event_type: EventType;
  location: string;
  is_virtual: boolean;
  virtual_link: string | null;
  banner_url: string | null;
  start_date: string;
  end_date: string;
  registration_deadline: string;
  max_participants: number | null;
}

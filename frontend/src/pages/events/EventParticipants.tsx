import { ArrowLeft } from "lucide-react";
import { useParams } from "react-router-dom";
import { errorMessage, isNotFoundError } from "../../api/client";
import Badge from "../../components/Badge";
import Card from "../../components/Card";
import Checkbox from "../../components/Checkbox";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import StatTile from "../../components/StatTile";
import { useSetAttendance } from "../../hooks/useEventActions";
import { useEvent, useParticipants } from "../../hooks/useEvents";
import { useToast } from "../../hooks/useToast";
import type { Participant } from "../../types/events";
import {
  REGISTRATION_STATUS_TONES,
  eventWhen,
  formatDateTime,
} from "../../utils/eventLabels";
import { EventNotFound } from "./EventNotFound";

// Organiser labels: the member-facing ones ("You're going") read oddly here.
const STATUS_LABELS = { CONFIRMED: "Confirmed", WAITLISTED: "Waitlisted", CANCELLED: "Cancelled" } as const;

function ParticipantRow({ eventId, participant }: { eventId: string; participant: Participant }) {
  const { showToast } = useToast();
  const setAttendance = useSetAttendance();
  const attended = participant.attended_at !== null;

  function toggle(next: boolean) {
    setAttendance.mutate(
      { eventId, registrationId: participant.id, attended: next },
      {
        onError: (error) =>
          showToast(errorMessage(error, `Couldn't update ${participant.student_name}'s attendance.`), "error"),
      },
    );
  }

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 p-4">
      <div className="min-w-0">
        <p className="font-medium wrap-anywhere text-white">{participant.student_name}</p>
        <p className="text-xs wrap-anywhere text-white/50">
          {participant.student_email} · registered {formatDateTime(participant.registered_at)}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={REGISTRATION_STATUS_TONES[participant.status]}>{STATUS_LABELS[participant.status]}</Badge>
        {participant.status === "CONFIRMED" && (
          <Checkbox
            id={`attended-${participant.id}`}
            label="Attended"
            checked={attended}
            disabled={setAttendance.isPending}
            onChange={toggle}
          />
        )}
      </div>
    </li>
  );
}

// Who signed up, in the order they did, and a check-in box per confirmed person.
export function EventParticipants() {
  const { id = "" } = useParams();
  const event = useEvent(id);
  const participants = useParticipants(id);

  if (event.isPending || participants.isPending) {
    return (
      <div aria-busy="true" aria-label="Loading participants" className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }
  if (!event.data) {
    return isNotFoundError(event.error) ? (
      <EventNotFound />
    ) : (
      <ErrorState onRetry={() => void event.refetch()} isRetrying={event.isFetching} />
    );
  }
  if (!participants.data) {
    return <ErrorState onRetry={() => void participants.refetch()} isRetrying={participants.isFetching} />;
  }

  const rows = participants.data;
  const confirmed = rows.filter((p) => p.status === "CONFIRMED");
  const waitlisted = rows.filter((p) => p.status === "WAITLISTED");
  const cancelled = rows.filter((p) => p.status === "CANCELLED");
  const attended = confirmed.filter((p) => p.attended_at !== null).length;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PrefetchLink
        to={`/events/${id}`}
        className="-my-3 inline-flex items-center gap-1 py-3 text-sm text-sees-mustard hover:text-sees-mint"
      >
        <ArrowLeft aria-hidden="true" className="size-4" />
        Back to the event
      </PrefetchLink>
      <div>
        <h1 className="text-3xl font-semibold wrap-anywhere text-sees-mint">{event.data.title}</h1>
        <p className="mt-1 text-white/60">{eventWhen(event.data)}</p>
      </div>

      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
        <li>
          <StatTile
            label="Confirmed"
            value={confirmed.length}
            detail={event.data.max_participants === null ? "No limit" : `of ${event.data.max_participants} places`}
          />
        </li>
        <li>
          <StatTile label="Attended" value={attended} detail={confirmed.length ? `${Math.round((attended / confirmed.length) * 100)}% of confirmed` : undefined} />
        </li>
        <li>
          <StatTile label="Waitlisted" value={waitlisted.length} />
        </li>
        <li>
          <StatTile label="Cancelled" value={cancelled.length} />
        </li>
      </ul>

      {rows.length === 0 ? (
        <EmptyState title="Nobody has registered yet" message="Registrations will appear here as they come in." />
      ) : (
        [
          { title: "Confirmed", items: confirmed },
          { title: "Waitlist, in order", items: waitlisted },
          { title: "Cancelled", items: cancelled },
        ]
          .filter((group) => group.items.length > 0)
          .map((group) => (
            <section key={group.title} aria-label={group.title} className="space-y-3">
              <h2 className="text-lg font-medium text-white">{group.title}</h2>
              <Card padding="none">
                <ul className="divide-y divide-sees-teal/40">
                  {group.items.map((participant) => (
                    <ParticipantRow key={participant.id} eventId={id} participant={participant} />
                  ))}
                </ul>
              </Card>
            </section>
          ))
      )}
    </div>
  );
}

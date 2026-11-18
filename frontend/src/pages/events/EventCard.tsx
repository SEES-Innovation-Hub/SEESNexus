import { CalendarDays, MapPin, Users, Video } from "lucide-react";
import Badge from "../../components/Badge";
import PrefetchLink from "../../components/PrefetchLink";
import type { RegistrationStatus, SeesEvent } from "../../types/events";
import {
  EVENT_TYPE_LABELS,
  REGISTRATION_STATUS_LABELS,
  REGISTRATION_STATUS_TONES,
  eventWhen,
  hasStarted,
  placesSummary,
} from "../../utils/eventLabels";

interface EventCardProps {
  event: SeesEvent;
  // The viewer's own registration, if any (not CANCELLED).
  myStatus?: RegistrationStatus;
}

// One event in a grid. The whole card opens the event (the title's link is
// stretched over it), like ProjectCard.
export function EventCard({ event, myStatus }: EventCardProps) {
  const past = hasStarted(event);
  return (
    <article
      className={`relative h-full overflow-hidden rounded-2xl border border-sees-teal/40 bg-gradient-card shadow-sees-card transition-colors hover:border-sees-mint/50 ${past ? "opacity-75" : ""}`}
    >
      {event.banner_url ? (
        <img
          src={event.banner_url}
          alt=""
          width={576}
          height={240}
          loading="lazy"
          decoding="async"
          className="aspect-[12/5] w-full object-cover"
        />
      ) : (
        <div
          aria-hidden="true"
          className="flex h-16 w-full items-center justify-center bg-sees-glass font-mono text-sm text-sees-mint/60"
        >
          {EVENT_TYPE_LABELS[event.event_type]}
        </div>
      )}
      <div className="space-y-3 p-4">
        <div className="flex flex-wrap gap-2">
          <Badge tone="mint">{EVENT_TYPE_LABELS[event.event_type]}</Badge>
          {myStatus && (
            <Badge tone={REGISTRATION_STATUS_TONES[myStatus]}>{REGISTRATION_STATUS_LABELS[myStatus]}</Badge>
          )}
          {event.deleted_at && <Badge tone="red">Deleted</Badge>}
          {past && !event.deleted_at && <Badge>Past</Badge>}
        </div>
        <h3 className="text-lg font-semibold wrap-anywhere text-white">
          <PrefetchLink
            to={`/events/${event.id}`}
            className="after:absolute after:inset-0 after:rounded-2xl focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:outline-sees-mint"
          >
            {event.title}
          </PrefetchLink>
        </h3>
        <ul className="space-y-1.5 text-sm text-white/70">
          <li className="flex gap-2">
            <CalendarDays aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sees-mint/70" />
            <span>{eventWhen(event)}</span>
          </li>
          <li className="flex gap-2">
            {event.is_virtual ? (
              <Video aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sees-mint/70" />
            ) : (
              <MapPin aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sees-mint/70" />
            )}
            <span className="wrap-anywhere">{event.location}</span>
          </li>
          <li className="flex gap-2">
            <Users aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sees-mint/70" />
            <span>{placesSummary(event)}</span>
          </li>
        </ul>
      </div>
    </article>
  );
}

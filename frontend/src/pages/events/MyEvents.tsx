import { buttonClassName } from "../../components/Button/buttonClassName";
import Badge from "../../components/Badge";
import Card from "../../components/Card";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useMyRegistrations } from "../../hooks/useEvents";
import type { MyRegistration } from "../../types/events";
import {
  EVENT_TYPE_LABELS,
  REGISTRATION_STATUS_LABELS,
  REGISTRATION_STATUS_TONES,
  eventWhen,
  hasStarted,
} from "../../utils/eventLabels";

function RegistrationRow({ registration }: { registration: MyRegistration }) {
  const { event } = registration;
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 p-4">
      <div className="min-w-0 space-y-1">
        {registration.event_deleted ? (
          <p className="font-medium wrap-anywhere text-white/60">{event.title}</p>
        ) : (
          <PrefetchLink
            to={`/events/${event.id}`}
            className="-my-2.5 block py-2.5 font-medium wrap-anywhere text-white hover:text-sees-mint"
          >
            {event.title}
          </PrefetchLink>
        )}
        <p className="text-xs wrap-anywhere text-white/50">
          {EVENT_TYPE_LABELS[event.event_type]} · {eventWhen(event)} · {event.location}
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {registration.event_deleted ? (
          <Badge tone="red">Called off</Badge>
        ) : (
          <>
            <Badge tone={REGISTRATION_STATUS_TONES[registration.status]}>
              {REGISTRATION_STATUS_LABELS[registration.status]}
              {registration.waitlist_position !== null && ` · #${registration.waitlist_position}`}
            </Badge>
            {registration.attended_at && <Badge tone="mint">Attended</Badge>}
          </>
        )}
      </div>
    </li>
  );
}

// Everything the member signed up for: what's coming, then what's past or
// cancelled. Works after a registration deadline, which is the point of it.
export function MyEvents() {
  const { data, isPending, isError, isFetching, refetch } = useMyRegistrations();

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading your events" className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-40 rounded-2xl" />
      </div>
    );
  }
  if (isError) return <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />;

  const isComing = (r: MyRegistration) => r.status !== "CANCELLED" && !r.event_deleted && !hasStarted(r.event);
  // The API sends newest first; coming up reads better soonest first.
  const comingUp = data.filter(isComing).reverse();
  const earlier = data.filter((r) => !isComing(r));

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">My events</h1>
        <p className="mt-1 text-white/60">Events you've registered for, and where you stand.</p>
      </div>

      {data.length === 0 ? (
        <EmptyState
          title="You haven't registered for anything yet"
          message="Find a hackathon, workshop or orientation and save your place."
          action={
            <PrefetchLink to="/events" className={buttonClassName()}>
              Browse events
            </PrefetchLink>
          }
        />
      ) : (
        <>
          <section aria-labelledby="coming-heading" className="space-y-4">
            <h2 id="coming-heading" className="text-lg font-medium text-white">
              Coming up
            </h2>
            {comingUp.length > 0 ? (
              <Card padding="none">
                <ul className="divide-y divide-sees-teal/40">
                  {comingUp.map((r) => (
                    <RegistrationRow key={r.id} registration={r} />
                  ))}
                </ul>
              </Card>
            ) : (
              <p className="text-sm text-white/50">Nothing coming up.</p>
            )}
          </section>
          {earlier.length > 0 && (
            <section aria-labelledby="earlier-heading" className="space-y-4">
              <h2 id="earlier-heading" className="text-lg font-medium text-white">
                Past and cancelled
              </h2>
              <Card padding="none">
                <ul className="divide-y divide-sees-teal/40">
                  {earlier.map((r) => (
                    <RegistrationRow key={r.id} registration={r} />
                  ))}
                </ul>
              </Card>
            </section>
          )}
        </>
      )}
    </div>
  );
}

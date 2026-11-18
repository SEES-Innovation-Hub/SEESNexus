import { ExternalLink } from "lucide-react";
import { useState } from "react";
import { errorMessage } from "../../api/client";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import ConfirmDialog from "../../components/ConfirmDialog";
import { useCancelRegistration, useRegisterForEvent } from "../../hooks/useEventActions";
import { useMyRegistrations } from "../../hooks/useEvents";
import { useToast } from "../../hooks/useToast";
import type { SeesEvent } from "../../types/events";
import {
  REGISTRATION_STATUS_LABELS,
  REGISTRATION_STATUS_TONES,
  formatDateTime,
  hasStarted,
  inCheckInWindow,
  registrationClosed,
} from "../../utils/eventLabels";
import { isHttpUrl } from "../../utils/isHttpUrl";
import { CheckInForm } from "./CheckInForm";

// The member's side of an event: where they stand and what they can do next.
export function RegistrationPanel({ event }: { event: SeesEvent }) {
  const { showToast } = useToast();
  const mine = useMyRegistrations();
  const register = useRegisterForEvent();
  const cancel = useCancelRegistration();
  const [confirmingCancel, setConfirmingCancel] = useState(false);

  const registration = mine.data?.find((r) => r.event_id === event.id && r.status !== "CANCELLED");
  const started = hasStarted(event);
  const closed = registrationClosed(event);
  const full = event.spots_left === 0;

  function handleRegister() {
    register.mutate(event.id, {
      onSuccess: (result) =>
        showToast(
          result.status === "CONFIRMED"
            ? "You're registered."
            : "The event is full, so you're on the waitlist. We'll email you if a place opens up.",
        ),
      onError: (error) => showToast(errorMessage(error, "Couldn't register. Try again."), "error"),
    });
  }

  function handleCancel() {
    cancel.mutate(event.id, {
      onSuccess: () => showToast("Registration cancelled"),
      onError: (error) => showToast(errorMessage(error, "Couldn't cancel. Try again."), "error"),
      onSettled: () => setConfirmingCancel(false),
    });
  }

  if (mine.isPending) return <p className="text-sm text-white/50">Checking your registration…</p>;

  return (
    <section aria-labelledby="registration-heading" className="space-y-3">
      <h2 id="registration-heading" className="sr-only">
        Your registration
      </h2>

      {registration ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={REGISTRATION_STATUS_TONES[registration.status]}>
              {REGISTRATION_STATUS_LABELS[registration.status]}
            </Badge>
            {registration.attended_at && <Badge tone="mint">Attended</Badge>}
            {registration.status === "WAITLISTED" && registration.waitlist_position !== null && (
              <span className="text-sm text-white/70">
                Number {registration.waitlist_position} in line. You'll be emailed if a place opens up.
              </span>
            )}
          </div>

          {registration.status === "CONFIRMED" &&
            !registration.attended_at &&
            event.checkin_open &&
            inCheckInWindow(event) && <CheckInForm eventId={event.id} />}

          <div className="flex flex-wrap gap-3">
            {registration.status === "CONFIRMED" && event.is_virtual && isHttpUrl(event.virtual_link) && (
              <a href={event.virtual_link} target="_blank" rel="noreferrer" className={buttonClassName()}>
                <ExternalLink aria-hidden="true" className="size-4" />
                Join the meeting
              </a>
            )}
            {!started && (
              <Button variant="secondary" onClick={() => setConfirmingCancel(true)}>
                Cancel my registration
              </Button>
            )}
          </div>
        </div>
      ) : started ? (
        <p className="text-sm text-white/60">This event has already started.</p>
      ) : closed ? (
        <p className="text-sm text-white/60">Registration closed {formatDateTime(event.registration_deadline)}.</p>
      ) : (
        <div className="space-y-2">
          <Button onClick={handleRegister} isLoading={register.isPending}>
            {full ? "Join the waitlist" : "Register"}
          </Button>
          <p className="text-xs text-white/50">
            Registration closes {formatDateTime(event.registration_deadline)}.
            {full && " Every place is taken; you'll move up if someone cancels."}
          </p>
        </div>
      )}

      <ConfirmDialog
        open={confirmingCancel}
        title="Cancel your registration?"
        message={
          registration?.status === "CONFIRMED"
            ? "Your place will go to the next person on the waitlist. If you change your mind you'll need to register again, and may end up waitlisted."
            : "You'll leave the waitlist. If you register again you'll join the back of the line."
        }
        confirmLabel="Cancel registration"
        onConfirm={handleCancel}
        onCancel={() => setConfirmingCancel(false)}
        isPending={cancel.isPending}
      />
    </section>
  );
}

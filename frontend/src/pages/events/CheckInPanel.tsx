import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import Card from "../../components/Card";
import { useCloseCheckIn, useOpenCheckIn } from "../../hooks/useEventActions";
import { useToast } from "../../hooks/useToast";
import type { SeesEvent } from "../../types/events";

// The organiser's side of self check-in: open it, show the code big enough to
// put on a projector, swap it if it leaks, close it.
export function CheckInPanel({ event }: { event: SeesEvent }) {
  const { showToast } = useToast();
  const open = useOpenCheckIn();
  const close = useCloseCheckIn();
  const busy = open.isPending || close.isPending;
  const fail = (fallback: string) => (error: unknown) => showToast(errorMessage(error, fallback), "error");

  function openOrRenew(renewing: boolean) {
    open.mutate(event.id, {
      onSuccess: () => showToast(renewing ? "New code ready. The old one no longer works." : "Check-in is open"),
      onError: fail(renewing ? "Couldn't make a new code." : "Couldn't open check-in."),
    });
  }

  function closeCheckIn() {
    close.mutate(event.id, {
      onSuccess: () => showToast("Check-in closed"),
      onError: fail("Couldn't close check-in."),
    });
  }

  return (
    <Card as="section" aria-labelledby="checkin-heading" className="space-y-4">
      <div>
        <h2 id="checkin-heading" className="text-lg font-medium text-white">
          Self check-in
        </h2>
        <p className="text-sm text-white/60">
          Members with a confirmed place enter this code on the event page, from an hour before the start until
          the end. You can still tick people off below.
        </p>
      </div>
      {event.checkin_open && event.checkin_code ? (
        <>
          <p
            aria-label={`Check-in code ${event.checkin_code.split("").join(" ")}`}
            className="rounded-xl bg-sees-void/70 py-6 text-center font-mono text-5xl font-semibold tracking-[0.3em] text-sees-mint sm:text-6xl"
          >
            {event.checkin_code}
          </p>
          <div className="flex flex-wrap gap-3">
            <Button
              variant="secondary"
              disabled={busy}
              isLoading={open.isPending}
              onClick={() => openOrRenew(true)}
            >
              New code
            </Button>
            <Button
              variant="secondary"
              disabled={busy}
              isLoading={close.isPending}
              onClick={closeCheckIn}
            >
              Close check-in
            </Button>
          </div>
        </>
      ) : (
        <Button
          isLoading={open.isPending}
          onClick={() => openOrRenew(false)}
        >
          Open check-in
        </Button>
      )}
    </Card>
  );
}

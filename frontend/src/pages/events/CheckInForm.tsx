import { useState, type FormEvent } from "react";
import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import TextField from "../../components/TextField";
import { useCheckIn } from "../../hooks/useEventActions";
import { useToast } from "../../hooks/useToast";

// For a confirmed member while check-in is open: type the code shown at the event.
export function CheckInForm({ eventId }: { eventId: string }) {
  const { showToast } = useToast();
  const checkIn = useCheckIn();
  const [code, setCode] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!code.trim()) return;
    checkIn.mutate(
      { eventId, code: code.trim() },
      {
        onSuccess: () => showToast("You're checked in. Enjoy the event!"),
        onError: (error) => showToast(errorMessage(error, "Couldn't check you in. Try again."), "error"),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded-xl border border-sees-mint/30 bg-sees-mint/5 p-4">
      <div className="w-40">
        <TextField
          id="checkin-code"
          label="Check-in code"
          value={code}
          onChange={(value) => setCode(value.toUpperCase())}
          maxLength={12}
          autoComplete="off"
          placeholder="ABC234"
        />
      </div>
      <Button type="submit" isLoading={checkIn.isPending}>
        Check in
      </Button>
      <p className="w-full text-xs text-white/60">The organisers will show the code at the event.</p>
    </form>
  );
}

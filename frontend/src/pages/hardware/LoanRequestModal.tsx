import { useState, type FormEvent } from "react";
import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import TextArea from "../../components/TextArea";
import TextField from "../../components/TextField";
import { useRequestLoan } from "../../hooks/useRequestLoan";
import { useToast } from "../../hooks/useToast";
import type { Hardware } from "../../types/hardware";

const PURPOSE_MAX = 1000;

// Tomorrow as YYYY-MM-DD in the viewer's own time zone, the earliest sensible
// return date (the date input's min).
function tomorrow() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

interface LoanRequestFormProps {
  item: Hardware;
  onCancel: () => void;
  onRequested: () => void;
}

function LoanRequestForm({ item, onCancel, onRequested }: LoanRequestFormProps) {
  const [purpose, setPurpose] = useState("");
  const [returnDate, setReturnDate] = useState("");
  const [purposeError, setPurposeError] = useState<string>();
  const requestLoan = useRequestLoan();
  const { showToast } = useToast();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!purpose.trim()) {
      setPurposeError("Say briefly what you need it for.");
      document.getElementById("loan-purpose")?.focus();
      return;
    }
    requestLoan.mutate(
      {
        hardwareId: item.id,
        payload: {
          purpose: purpose.trim(),
          // The end of the chosen day, in the borrower's own time zone.
          expected_return_date: returnDate ? new Date(`${returnDate}T23:59:59`).toISOString() : null,
        },
      },
      {
        onSuccess: () => {
          showToast("Loan requested. An admin will review it.");
          onRequested();
        },
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <TextArea
        id="loan-purpose"
        label="What do you need it for?"
        required
        value={purpose}
        onChange={(value) => {
          setPurpose(value);
          setPurposeError(undefined);
        }}
        maxLength={PURPOSE_MAX}
        hint="e.g. Testing the power supply for our final-year project."
        error={purposeError}
      />
      <TextField
        id="loan-return-date"
        label="When will you bring it back?"
        type="date"
        required={false}
        min={tomorrow()}
        value={returnDate}
        onChange={setReturnDate}
      />
      {requestLoan.error && (
        <p role="alert" className="text-sm wrap-anywhere text-red-400">
          {errorMessage(requestLoan.error, "Couldn't send the request. Try again.")}
        </p>
      )}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onCancel} disabled={requestLoan.isPending}>
          Cancel
        </Button>
        <Button type="submit" isLoading={requestLoan.isPending}>
          Send request
        </Button>
      </div>
    </form>
  );
}

interface LoanRequestModalProps {
  item: Hardware | null;
  onClose: () => void;
  onRequested: (item: Hardware) => void;
}

// Stays mounted while closed, so the browser can return focus to the card's
// button when it's cancelled. The form inside is keyed by item, so each
// request starts empty.
export function LoanRequestModal({ item, onClose, onRequested }: LoanRequestModalProps) {
  return (
    <Modal open={item !== null} onClose={onClose} title={item ? `Borrow ${item.name}` : "Borrow"}>
      {item && (
        <LoanRequestForm key={item.id} item={item} onCancel={onClose} onRequested={() => onRequested(item)} />
      )}
    </Modal>
  );
}

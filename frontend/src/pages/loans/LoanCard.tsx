import { useState } from "react";
import { errorMessage } from "../../api/client";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import { useCancelLoanRequest } from "../../hooks/useCancelLoanRequest";
import { useToast } from "../../hooks/useToast";
import type { Loan } from "../../types/hardware";
import { LOAN_STATUS_LABELS, LOAN_STATUS_TONES } from "../../utils/hardwareLabels";
import { isOverdue } from "../../utils/isOverdue";
import { loanDateSummary } from "../../utils/loanDates";

export function LoanCard({ loan }: { loan: Loan }) {
  const { showToast } = useToast();
  const cancel = useCancelLoanRequest();
  const [confirming, setConfirming] = useState(false);
  const item = loan.hardware_name ?? "this item";

  function handleWithdraw() {
    cancel.mutate(loan.id, {
      onSuccess: () => showToast("Request withdrawn"),
      onError: (error) => showToast(errorMessage(error, "Couldn't withdraw the request. Try again."), "error"),
      onSettled: () => setConfirming(false),
    });
  }

  return (
    <Card as="article" className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-lg font-semibold wrap-anywhere text-white">{loan.hardware_name ?? "Unknown item"}</h3>
        <div className="flex flex-wrap gap-2">
          {isOverdue(loan) && <Badge tone="red">Overdue</Badge>}
          <Badge tone={LOAN_STATUS_TONES[loan.status]}>{LOAN_STATUS_LABELS[loan.status]}</Badge>
        </div>
      </div>
      <p className="text-sm wrap-anywhere whitespace-pre-line text-white/70">{loan.purpose}</p>
      <p className="text-xs text-white/50">{loanDateSummary(loan)}</p>
      {/* Students can't mark a loan returned themselves: an admin checks the
          item back in once it's physically at the lab. */}
      {loan.status === "APPROVED" && (
        <p className="text-sm text-sees-mustard">Bring it back to the lab. An admin will check it in.</p>
      )}
      {loan.status === "PENDING" && (
        <Button variant="secondary" onClick={() => setConfirming(true)}>
          Withdraw request
        </Button>
      )}

      <ConfirmDialog
        open={confirming}
        title="Withdraw this request?"
        message={`Your request for ${item} will be closed. You can ask again later.`}
        confirmLabel="Withdraw request"
        onConfirm={handleWithdraw}
        onCancel={() => setConfirming(false)}
        isPending={cancel.isPending}
      />
    </Card>
  );
}

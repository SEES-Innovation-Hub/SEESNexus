import { useState } from "react";
import { errorMessage } from "../../api/client";
import Avatar from "../../components/Avatar";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import { useApproveLoan } from "../../hooks/useApproveLoan";
import { useRejectLoan } from "../../hooks/useRejectLoan";
import { useReturnLoan } from "../../hooks/useReturnLoan";
import { useToast } from "../../hooks/useToast";
import type { User } from "../../types/auth";
import type { Loan } from "../../types/hardware";
import { LOAN_STATUS_LABELS, LOAN_STATUS_TONES } from "../../utils/hardwareLabels";
import { isOverdue } from "../../utils/isOverdue";
import { loanDateSummary } from "../../utils/loanDates";

interface AdminLoanCardProps {
  loan: Loan;
  // undefined while the member list is still loading.
  borrower: User | undefined;
}

// One loan for an admin: what, who, why, when, and the next step: a decision
// while pending, checking the item back in while it's out. Approving needs no
// confirmation; rejecting and returning do.
export function AdminLoanCard({ loan, borrower }: AdminLoanCardProps) {
  const approve = useApproveLoan();
  const reject = useRejectLoan();
  const giveBack = useReturnLoan();
  const { showToast } = useToast();
  const [confirmingReject, setConfirmingReject] = useState(false);
  const [confirmingReturn, setConfirmingReturn] = useState(false);
  const item = loan.hardware_name ?? "this item";
  const who = borrower?.full_name ?? "the member";

  function handleApprove() {
    approve.mutate(loan.id, {
      onSuccess: () => showToast(`Approved: ${item} is now on loan to ${who}.`),
      onError: (error) => showToast(errorMessage(error, "Couldn't approve the request. Try again."), "error"),
    });
  }

  function handleReject() {
    reject.mutate(loan.id, {
      onSuccess: () => showToast(`Rejected ${who}'s request for ${item}.`),
      onError: (error) => showToast(errorMessage(error, "Couldn't reject the request. Try again."), "error"),
      onSettled: () => setConfirmingReject(false),
    });
  }

  function handleReturn() {
    giveBack.mutate(loan.id, {
      onSuccess: () => showToast(`${item} is back on the shelf.`),
      onError: (error) => showToast(errorMessage(error, "Couldn't check the item in. Try again."), "error"),
      onSettled: () => setConfirmingReturn(false),
    });
  }

  return (
    <Card as="article" className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-lg font-semibold wrap-anywhere text-white">
          {item}
        </h3>
        <div className="flex flex-wrap gap-2">
          {isOverdue(loan) && <Badge tone="red">Overdue</Badge>}
          <Badge tone={LOAN_STATUS_TONES[loan.status]}>{LOAN_STATUS_LABELS[loan.status]}</Badge>
        </div>
      </div>

      <div className="flex items-center gap-3 text-sm">
        {borrower && <Avatar name={borrower.full_name} imageUrl={borrower.profile_image_url} />}
        <div className="min-w-0">
          <p className="wrap-anywhere text-white">{borrower?.full_name ?? "Loading member…"}</p>
          {borrower && (
            <p className="wrap-anywhere text-white/50">
              {borrower.email}
              {borrower.department && ` · ${borrower.department}`}
              {borrower.level && ` · ${borrower.level}`}
            </p>
          )}
        </div>
      </div>

      <p className="text-sm wrap-anywhere whitespace-pre-line text-white/70">{loan.purpose}</p>
      <p className="text-xs text-white/50">{loanDateSummary(loan)}</p>

      {loan.status === "PENDING" && (
        <div className="flex flex-wrap gap-3 pt-1">
          <Button onClick={handleApprove} isLoading={approve.isPending} disabled={reject.isPending}>
            Approve
          </Button>
          <Button
            variant="secondary"
            onClick={() => setConfirmingReject(true)}
            disabled={approve.isPending || reject.isPending}
          >
            Reject
          </Button>
        </div>
      )}

      {loan.status === "APPROVED" && (
        <div className="pt-1">
          <Button variant="secondary" onClick={() => setConfirmingReturn(true)}>
            Mark returned
          </Button>
        </div>
      )}

      <ConfirmDialog
        open={confirmingReturn}
        title="Check this item back in?"
        message={`Only do this once ${item} is physically back at the lab. It becomes available to borrow again.`}
        confirmLabel="Mark returned"
        tone="primary"
        onConfirm={handleReturn}
        onCancel={() => setConfirmingReturn(false)}
        isPending={giveBack.isPending}
      />

      <ConfirmDialog
        open={confirmingReject}
        title="Reject this request?"
        message={`${who} asked to borrow ${item}. They'll see it as rejected in My Loans.`}
        confirmLabel="Reject request"
        onConfirm={handleReject}
        onCancel={() => setConfirmingReject(false)}
        isPending={reject.isPending}
      />
    </Card>
  );
}

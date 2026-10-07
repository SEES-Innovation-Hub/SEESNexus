import Badge from "../../components/Badge";
import Button from "../../components/Button";
import Card from "../../components/Card";
import type { Loan } from "../../types/hardware";
import { LOAN_STATUS_LABELS, LOAN_STATUS_TONES } from "../../utils/hardwareLabels";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(undefined, { dateStyle: "medium" });
}

interface LoanCardProps {
  loan: Loan;
  // undefined while the item's name is still being looked up.
  hardwareName: string | undefined;
  onReturn: () => void;
}

export function LoanCard({ loan, hardwareName, onReturn }: LoanCardProps) {
  const isOverdue =
    loan.status === "APPROVED" &&
    loan.expected_return_date !== null &&
    new Date(loan.expected_return_date) < new Date();

  // Only the dates that have happened (or are due) for this loan's state.
  const dates = [
    loan.request_date && `Requested ${formatDate(loan.request_date)}`,
    loan.approval_date && `${loan.status === "REJECTED" ? "Rejected" : "Approved"} ${formatDate(loan.approval_date)}`,
    loan.status !== "RETURNED" && loan.status !== "REJECTED" && loan.expected_return_date &&
      `Due back ${formatDate(loan.expected_return_date)}`,
    loan.actual_return_date && `Returned ${formatDate(loan.actual_return_date)}`,
  ].filter(Boolean);

  return (
    <Card as="article" className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-lg font-semibold wrap-anywhere text-white">
          {hardwareName ?? <span className="text-white/40">Loading item…</span>}
        </h3>
        <div className="flex flex-wrap gap-2">
          {isOverdue && <Badge tone="red">Overdue</Badge>}
          <Badge tone={LOAN_STATUS_TONES[loan.status]}>{LOAN_STATUS_LABELS[loan.status]}</Badge>
        </div>
      </div>
      <p className="text-sm wrap-anywhere whitespace-pre-line text-white/70">{loan.purpose}</p>
      <p className="text-xs text-white/50">{dates.join(" · ")}</p>
      {loan.status === "APPROVED" && (
        <Button variant="secondary" onClick={onReturn}>
          Mark as returned
        </Button>
      )}
    </Card>
  );
}

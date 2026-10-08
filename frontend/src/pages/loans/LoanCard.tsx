import Badge from "../../components/Badge";
import Button from "../../components/Button";
import Card from "../../components/Card";
import type { Loan } from "../../types/hardware";
import { LOAN_STATUS_LABELS, LOAN_STATUS_TONES } from "../../utils/hardwareLabels";
import { isOverdue } from "../../utils/isOverdue";
import { loanDateSummary } from "../../utils/loanDates";

interface LoanCardProps {
  loan: Loan;
  // undefined while the item's name is still being looked up.
  hardwareName: string | undefined;
  onReturn: () => void;
}

export function LoanCard({ loan, hardwareName, onReturn }: LoanCardProps) {
  return (
    <Card as="article" className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-lg font-semibold wrap-anywhere text-white">
          {hardwareName ?? <span className="text-white/40">Loading item…</span>}
        </h3>
        <div className="flex flex-wrap gap-2">
          {isOverdue(loan) && <Badge tone="red">Overdue</Badge>}
          <Badge tone={LOAN_STATUS_TONES[loan.status]}>{LOAN_STATUS_LABELS[loan.status]}</Badge>
        </div>
      </div>
      <p className="text-sm wrap-anywhere whitespace-pre-line text-white/70">{loan.purpose}</p>
      <p className="text-xs text-white/50">{loanDateSummary(loan)}</p>
      {loan.status === "APPROVED" && (
        <Button variant="secondary" onClick={onReturn}>
          Mark as returned
        </Button>
      )}
    </Card>
  );
}

import type { Loan } from "../types/hardware";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(undefined, { dateStyle: "medium" });
}

// One line of the dates that matter for the loan's state, e.g.
// "Requested 7 Oct 2026 · Approved 8 Oct 2026 · Due back 14 Oct 2026".
export function loanDateSummary(loan: Loan): string {
  const isOpen = loan.status === "PENDING" || loan.status === "APPROVED";
  return [
    loan.request_date && `Requested ${formatDate(loan.request_date)}`,
    loan.approval_date &&
      `${loan.status === "REJECTED" ? "Rejected" : "Approved"} ${formatDate(loan.approval_date)}`,
    isOpen && loan.expected_return_date && `Due back ${formatDate(loan.expected_return_date)}`,
    loan.actual_return_date && `Returned ${formatDate(loan.actual_return_date)}`,
  ]
    .filter(Boolean)
    .join(" · ");
}

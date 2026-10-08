import type { Loan } from "../types/hardware";

// An item that is out on loan past the date the borrower said they'd return it.
export function isOverdue(loan: Loan): boolean {
  return (
    loan.status === "APPROVED" &&
    loan.expected_return_date !== null &&
    new Date(loan.expected_return_date) < new Date()
  );
}

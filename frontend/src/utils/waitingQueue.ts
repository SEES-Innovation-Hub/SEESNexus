import type { Loan } from "../types/hardware";

const time = (value: string | null) => (value ? new Date(value).getTime() : 0);

// Requests still waiting for an admin, oldest first: first come, first served.
export function waitingQueue(loans: Loan[]): Loan[] {
  return loans
    .filter((loan) => loan.status === "PENDING")
    .sort((a, b) => time(a.request_date) - time(b.request_date));
}

import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Skeleton from "../../components/Skeleton";
import { useAdminLoanList } from "../../hooks/useAdminLoanList";
import { useUrlFilters } from "../../hooks/useUrlFilters";
import type { Loan } from "../../types/hardware";
import { isOverdue } from "../../utils/isOverdue";
import { waitingQueue } from "../../utils/waitingQueue";
import { AdminLoanCard } from "./AdminLoanCard";

const VIEWS = {
  pending: { label: "Waiting", empty: "No requests waiting for a decision." },
  active: { label: "On loan", empty: "Nothing is out on loan right now." },
  history: { label: "History", empty: "No returned or rejected loans yet." },
  all: { label: "All", empty: "No loan requests yet." },
} as const;
type View = keyof typeof VIEWS;

function isView(value: string | null): value is View {
  return value !== null && Object.hasOwn(VIEWS, value);
}

// Waiting requests oldest first (waitingQueue); loans out right now put overdue
// ones first. The rest stay newest first, as the API sends them.
function loansFor(view: View, loans: Loan[]): Loan[] {
  switch (view) {
    case "pending":
      return waitingQueue(loans);
    case "active":
      return loans
        .filter((loan) => loan.status === "APPROVED")
        .sort((a, b) => Number(isOverdue(b)) - Number(isOverdue(a)));
    case "history":
      return loans.filter((loan) => loan.status === "RETURNED" || loan.status === "REJECTED");
    case "all":
      return loans;
  }
}

export function AdminLoans() {
  const { read, setFilter } = useUrlFilters();
  const view = read("view", isView) ?? "pending";
  const { loans, isPending, isError, isFetching, refetch, itemNames, borrowers } = useAdminLoanList();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Loan requests</h1>
        <p className="mt-1 text-white/60">Approve or reject requests, and see what's out on loan.</p>
      </div>

      {/* The view lives in the address bar (?view=active), so it survives a refresh. */}
      <div role="group" aria-label="Show" className="flex flex-wrap gap-1.5 sm:gap-2">
        {(Object.keys(VIEWS) as View[]).map((key) => (
          <button
            key={key}
            type="button"
            aria-pressed={view === key}
            onClick={() => setFilter("view", key === "pending" ? "" : key)}
            className={`inline-flex min-h-11 items-center gap-1.5 rounded-full border px-3 text-sm font-medium transition-colors sm:gap-2 sm:px-4 ${
              view === key
                ? "border-sees-mint bg-sees-mint/10 text-sees-mint"
                : "border-sees-teal text-white/70 hover:border-sees-mint/60 hover:text-white"
            }`}
          >
            {VIEWS[key].label}
            {loans && <span className="text-white/50 tabular-nums">{loansFor(key, loans).length}</span>}
          </button>
        ))}
      </div>

      {isPending && (
        <div aria-busy="true" aria-label="Loading loan requests" className="space-y-4">
          <Skeleton className="h-40 rounded-2xl" />
          <Skeleton className="h-40 rounded-2xl" />
        </div>
      )}
      {isError && !loans && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}

      {loans &&
        (loansFor(view, loans).length === 0 ? (
          <EmptyState title="Nothing here" message={VIEWS[view].empty} />
        ) : (
          <ul className="space-y-4">
            {loansFor(view, loans).map((loan) => (
              <li key={loan.id}>
                <AdminLoanCard
                  loan={loan}
                  itemName={itemNames[loan.hardware_id]}
                  borrower={borrowers.get(loan.borrower_id)}
                />
              </li>
            ))}
          </ul>
        ))}
    </div>
  );
}

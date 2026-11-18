import Badge from "../../components/Badge";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Card from "../../components/Card";
import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useMyLoans } from "../../hooks/useMyLoans";
import { LOAN_STATUS_LABELS, LOAN_STATUS_TONES } from "../../utils/hardwareLabels";
import { isOverdue } from "../../utils/isOverdue";
import { loanDateSummary } from "../../utils/loanDates";

// The member's loans still in progress, overdue first, in a compact list.
export function DashboardLoans() {
  const { data: loans, isPending, isError, isFetching, refetch } = useMyLoans();
  const current = (loans ?? [])
    .filter((loan) => loan.status === "PENDING" || loan.status === "APPROVED")
    .sort((a, b) => Number(isOverdue(b)) - Number(isOverdue(a)));

  return (
    <section aria-labelledby="dashboard-loans-heading" className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="dashboard-loans-heading" className="text-xl font-medium text-white">
          Your loans
        </h2>
        <PrefetchLink to="/loans" className="-my-3 py-3 text-sm text-sees-mustard underline hover:text-sees-mint">
          All my loans
        </PrefetchLink>
      </div>

      {isPending && <Skeleton className="h-24 rounded-2xl" />}
      {isError && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}
      {loans && current.length === 0 && (
        <Card className="flex flex-wrap items-center justify-between gap-4">
          <p className="text-sm text-white/60">Nothing borrowed or waiting for approval.</p>
          <PrefetchLink to="/hardware" className={buttonClassName("secondary")}>
            Browse hardware
          </PrefetchLink>
        </Card>
      )}
      {current.length > 0 && (
        <Card padding="none">
          <ul className="divide-y divide-sees-teal/40">
            {current.map((loan) => (
              <li key={loan.id} className="flex flex-wrap items-center justify-between gap-2 p-4">
                <div className="min-w-0">
                  <p className="font-medium wrap-anywhere text-white">
                    {loan.hardware_name ?? "Unknown item"}
                  </p>
                  <p className="text-xs text-white/50">{loanDateSummary(loan)}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {isOverdue(loan) && <Badge tone="red">Overdue</Badge>}
                  <Badge tone={LOAN_STATUS_TONES[loan.status]}>{LOAN_STATUS_LABELS[loan.status]}</Badge>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </section>
  );
}

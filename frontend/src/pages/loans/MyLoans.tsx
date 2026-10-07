import { useState } from "react";
import { errorMessage } from "../../api/client";
import { buttonClassName } from "../../components/Button/buttonClassName";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useHardwareNames } from "../../hooks/useHardwareNames";
import { useMyLoans } from "../../hooks/useMyLoans";
import { useReturnLoan } from "../../hooks/useReturnLoan";
import { useToast } from "../../hooks/useToast";
import type { Loan } from "../../types/hardware";
import { LoanCard } from "./LoanCard";

export function MyLoans() {
  const { data: loans, isPending, isError, isFetching, refetch } = useMyLoans();
  const names = useHardwareNames((loans ?? []).map((loan) => loan.hardware_id));
  const returnLoan = useReturnLoan();
  const { showToast } = useToast();
  const [returning, setReturning] = useState<Loan | null>(null);

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading your loans" className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-32 rounded-2xl" />
      </div>
    );
  }
  if (isError) return <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />;

  // Loans still in progress first; finished ones below as history.
  const current = loans.filter((loan) => loan.status === "PENDING" || loan.status === "APPROVED");
  const history = loans.filter((loan) => loan.status === "RETURNED" || loan.status === "REJECTED");

  function confirmReturn() {
    if (!returning) return;
    returnLoan.mutate(returning.id, {
      onSuccess: () => showToast("Marked as returned. Thank you!"),
      onError: (error) => showToast(errorMessage(error, "Couldn't mark it as returned. Try again."), "error"),
      onSettled: () => setReturning(null),
    });
  }

  const renderList = (items: Loan[]) => (
    <ul className="space-y-4">
      {items.map((loan) => (
        <li key={loan.id}>
          <LoanCard loan={loan} hardwareName={names[loan.hardware_id]} onReturn={() => setReturning(loan)} />
        </li>
      ))}
    </ul>
  );

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">My loans</h1>
        <p className="mt-1 text-white/60">Equipment you've asked for or borrowed from the lab.</p>
      </div>

      {loans.length === 0 ? (
        <EmptyState
          title="You haven't borrowed anything yet"
          message="Find what you need on the Hardware page and request a loan."
          action={
            <PrefetchLink to="/hardware" className={buttonClassName()}>
              Browse hardware
            </PrefetchLink>
          }
        />
      ) : (
        <>
          <section aria-labelledby="current-heading" className="space-y-4">
            <h2 id="current-heading" className="text-lg font-medium text-white">
              Current
            </h2>
            {current.length > 0 ? (
              renderList(current)
            ) : (
              <p className="text-sm text-white/50">Nothing on loan or waiting for approval.</p>
            )}
          </section>
          {history.length > 0 && (
            <section aria-labelledby="history-heading" className="space-y-4">
              <h2 id="history-heading" className="text-lg font-medium text-white">
                History
              </h2>
              {renderList(history)}
            </section>
          )}
        </>
      )}

      <ConfirmDialog
        open={returning !== null}
        title="Mark as returned?"
        message="Only do this once you've handed the item back to the lab."
        confirmLabel="Yes, I've returned it"
        tone="primary"
        onConfirm={confirmReturn}
        onCancel={() => setReturning(null)}
        isPending={returnLoan.isPending}
      />
    </div>
  );
}

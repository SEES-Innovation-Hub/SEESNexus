import { useState } from "react";
import Button from "../../components/Button";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Pagination from "../../components/Pagination";
import Select from "../../components/Select";
import Skeleton from "../../components/Skeleton";
import { useAuth } from "../../hooks/useAuth";
import { useHardwareList } from "../../hooks/useHardwareList";
import { useMyLoans } from "../../hooks/useMyLoans";
import { useUrlFilters } from "../../hooks/useUrlFilters";
import type { Hardware } from "../../types/hardware";
import {
  HARDWARE_CATEGORY_OPTIONS,
  HARDWARE_STATUS_OPTIONS,
  isHardwareCategory,
  isHardwareStatus,
} from "../../utils/hardwareLabels";
import { cardActionId } from "./cardActionId";
import { HardwareCard } from "./HardwareCard";
import { LoanRequestModal } from "./LoanRequestModal";

const PAGE_SIZE = 12;

export function HardwareList() {
  const { user } = useAuth();
  const { page, isFiltered, read, setFilter, setPage, clearAll } = useUrlFilters();
  const category = read("category", isHardwareCategory);
  const status = read("status", isHardwareStatus);
  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } = useHardwareList({
    page,
    pageSize: PAGE_SIZE,
    category,
    status,
  });
  const { data: myLoans } = useMyLoans();
  const [requesting, setRequesting] = useState<Hardware | null>(null);

  // Which items the viewer already has a pending or approved loan for.
  const activeLoans = new Map(
    (myLoans ?? [])
      .filter((loan) => loan.status === "PENDING" || loan.status === "APPROVED")
      .map((loan) => [loan.hardware_id, loan]),
  );

  // After a request the card's "Request loan" button is replaced by a link to
  // My Loans, so the dialog can't hand focus back to it. Focus the new link
  // instead, once the dialog has closed (two frames: close, then repaint).
  function handleRequested(item: Hardware) {
    setRequesting(null);
    requestAnimationFrame(() =>
      requestAnimationFrame(() => document.getElementById(cardActionId(item.id))?.focus()),
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Hardware</h1>
        <p className="mt-1 text-white/60">
          Equipment you can borrow from the SEES lab
          {data && data.total > 0 && ` · ${data.total} ${data.total === 1 ? "item" : "items"}`}
        </p>
      </div>

      <div className="grid max-w-xl gap-4 sm:grid-cols-2">
        <Select
          id="filter-category"
          label="Category"
          value={category ?? ""}
          onChange={(value) => setFilter("category", value)}
          options={HARDWARE_CATEGORY_OPTIONS}
          placeholder="All categories"
          required={false}
        />
        <Select
          id="filter-status"
          label="Availability"
          value={status ?? ""}
          onChange={(value) => setFilter("status", value)}
          options={HARDWARE_STATUS_OPTIONS}
          placeholder="Any"
          required={false}
        />
      </div>

      {isPending && (
        <div aria-busy="true" aria-label="Loading hardware" className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-64 rounded-2xl" />
          ))}
        </div>
      )}

      {isError && !data && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}

      {data && data.items.length === 0 &&
        (isFiltered ? (
          <EmptyState
            title="Nothing here"
            message="No equipment matches these filters."
            action={
              <Button variant="secondary" onClick={clearAll}>
                Show all hardware
              </Button>
            }
          />
        ) : (
          <EmptyState title="No equipment listed yet" message="Check back once the lab has added its inventory." />
        ))}

      {data && data.items.length > 0 && (
        <>
          <ul
            aria-busy={isPlaceholderData}
            className={`grid gap-5 transition-opacity sm:grid-cols-2 xl:grid-cols-3 ${isPlaceholderData ? "opacity-60" : ""}`}
          >
            {data.items.map((item) => (
              <li key={item.id}>
                <HardwareCard
                  item={item}
                  isSignedIn={user !== null}
                  activeLoan={activeLoans.get(item.id)}
                  onRequest={() => setRequesting(item)}
                />
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
        </>
      )}

      <LoanRequestModal item={requesting} onClose={() => setRequesting(null)} onRequested={handleRequested} />
    </div>
  );
}

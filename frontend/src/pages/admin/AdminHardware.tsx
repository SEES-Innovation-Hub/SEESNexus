import { Plus } from "lucide-react";
import { useState } from "react";
import Button from "../../components/Button";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Pagination from "../../components/Pagination";
import Select from "../../components/Select";
import Skeleton from "../../components/Skeleton";
import { useHardwareList } from "../../hooks/useHardwareList";
import { useUrlFilters } from "../../hooks/useUrlFilters";
import {
  HARDWARE_CATEGORY_OPTIONS,
  HARDWARE_STATUS_OPTIONS,
  isHardwareCategory,
  isHardwareStatus,
} from "../../utils/hardwareLabels";
import { AdminHardwareRow } from "./AdminHardwareRow";
import { HardwareFormModal, type HardwareFormTarget } from "./HardwareFormModal";

const PAGE_SIZE = 20;

export function AdminHardware() {
  const { page, isFiltered, read, setFilter, setPage, clearAll } = useUrlFilters();
  const category = read("category", isHardwareCategory);
  const status = read("status", isHardwareStatus);
  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } = useHardwareList({
    page,
    pageSize: PAGE_SIZE,
    category,
    status,
  });
  // undefined = form closed; null = adding; an item = editing it.
  const [editing, setEditing] = useState<HardwareFormTarget | undefined>(undefined);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-sees-mint">Hardware inventory</h1>
          <p className="mt-1 text-white/60">
            Add, edit and retire lab equipment
            {data && ` · ${data.total} ${data.total === 1 ? "item" : "items"}`}
          </p>
        </div>
        <Button onClick={() => setEditing(null)}>
          <Plus aria-hidden="true" className="size-4" />
          Add item
        </Button>
      </div>

      <div className="grid max-w-xl gap-4 sm:grid-cols-2">
        <Select
          id="inventory-category"
          label="Category"
          value={category ?? ""}
          onChange={(value) => setFilter("category", value)}
          options={HARDWARE_CATEGORY_OPTIONS}
          placeholder="All categories"
          required={false}
        />
        <Select
          id="inventory-status"
          label="Status"
          value={status ?? ""}
          onChange={(value) => setFilter("status", value)}
          options={HARDWARE_STATUS_OPTIONS}
          placeholder="Any"
          required={false}
        />
      </div>

      {isPending && (
        <div aria-busy="true" aria-label="Loading inventory" className="space-y-3">
          <Skeleton className="h-20 rounded-2xl" />
          <Skeleton className="h-20 rounded-2xl" />
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
                Show all
              </Button>
            }
          />
        ) : (
          <EmptyState title="The inventory is empty" message="Add the lab's first item." />
        ))}
      {data && data.items.length > 0 && (
        <>
          <ul aria-busy={isPlaceholderData} className={`space-y-3 transition-opacity ${isPlaceholderData ? "opacity-60" : ""}`}>
            {data.items.map((item) => (
              <li key={item.id}>
                <AdminHardwareRow item={item} onEdit={() => setEditing(item)} />
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
        </>
      )}

      <HardwareFormModal
        open={editing !== undefined}
        item={editing ?? null}
        onClose={() => setEditing(undefined)}
      />
    </div>
  );
}

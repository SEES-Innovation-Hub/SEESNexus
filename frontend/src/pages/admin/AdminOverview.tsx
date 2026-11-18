import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import StatTile from "../../components/StatTile";
import { useAdminLoanList } from "../../hooks/useAdminLoanList";
import { useAdminStats } from "../../hooks/useAdminStats";
import { useAuth } from "../../hooks/useAuth";
import { waitingQueue } from "../../utils/waitingQueue";
import { AdminLoanCard } from "./AdminLoanCard";

const PREVIEW_SIZE = 3;

// The admin's home: real counts from /admin/dashboard, then the oldest requests
// still waiting for a decision.
export function AdminOverview() {
  const { user } = useAuth();
  const stats = useAdminStats();
  const { loans, borrowers } = useAdminLoanList();
  const waiting = waitingQueue(loans ?? []).slice(0, PREVIEW_SIZE);

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Admin overview</h1>
        <p className="mt-1 wrap-anywhere text-white/60">Welcome back, {user?.full_name.split(" ")[0]}.</p>
      </div>

      {stats.isPending && (
        <div aria-busy="true" aria-label="Loading figures" className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-28 rounded-2xl" />
          ))}
        </div>
      )}
      {stats.isError && <ErrorState onRetry={() => void stats.refetch()} isRetrying={stats.isFetching} />}
      {stats.data && (
        <ul className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
          <li>
            <StatTile label="Requests waiting" value={stats.data.pending_loans} to="/admin/loans" detail="Need a decision" />
          </li>
          <li>
            <StatTile
              label="On loan now"
              value={stats.data.approved_loans}
              to="/admin/loans?view=active"
              detail={`Across ${stats.data.total_hardware_items} hardware ${stats.data.total_hardware_items === 1 ? "item" : "items"}`}
            />
          </li>
          <li>
            <StatTile
              label="Members"
              value={stats.data.total_users}
              detail={`${stats.data.active_users} active · ${stats.data.admins} ${stats.data.admins === 1 ? "admin" : "admins"}`}
            />
          </li>
          <li>
            <StatTile label="Projects" value={stats.data.total_projects} to="/projects" detail="Showcased by members" />
          </li>
          <li>
            <StatTile label="Events" value={stats.data.total_events} to="/events?view=all" detail="Not counting deleted ones" />
          </li>
          <li>
            <StatTile label="Articles" value={stats.data.total_articles} to="/articles" detail="Drafts included" />
          </li>
        </ul>
      )}

      <section aria-labelledby="waiting-heading" className="space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="waiting-heading" className="text-xl font-medium text-white">
            Waiting for you
          </h2>
          <PrefetchLink
            to="/admin/loans"
            className="-my-3 py-3 text-sm text-sees-mustard underline hover:text-sees-mint"
          >
            All loan requests
          </PrefetchLink>
        </div>
        {loans && waiting.length === 0 && (
          <p className="text-sm text-white/50">No requests waiting. You're all caught up.</p>
        )}
        <ul className="space-y-4">
          {waiting.map((loan) => (
            <li key={loan.id}>
              <AdminLoanCard loan={loan} borrower={borrowers.get(loan.borrower_id)} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

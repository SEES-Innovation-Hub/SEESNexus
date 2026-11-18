import { Cpu, Plus } from "lucide-react";
import { buttonClassName } from "../../components/Button/buttonClassName";
import PrefetchLink from "../../components/PrefetchLink";
import { useAuth } from "../../hooks/useAuth";
import { DashboardLoans } from "./DashboardLoans";
import { LatestProjects } from "./LatestProjects";

// A member's home page. Each section loads its own data, so one slow or failing
// request doesn't hold up the rest. Upcoming events join in Phase 4.
export function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-6xl space-y-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold wrap-anywhere text-sees-mint">
            Welcome back, {user?.full_name.split(" ")[0]}
          </h1>
          <p className="mt-1 text-white/60">Here's what's happening in SEES.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <PrefetchLink to="/projects/new" className={buttonClassName()}>
            <Plus aria-hidden="true" className="size-4" />
            New project
          </PrefetchLink>
          <PrefetchLink to="/hardware" className={buttonClassName("secondary")}>
            <Cpu aria-hidden="true" className="size-4" />
            Borrow hardware
          </PrefetchLink>
        </div>
      </div>

      <DashboardLoans />
      <LatestProjects />
    </div>
  );
}

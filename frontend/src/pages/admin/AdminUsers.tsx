import { useState } from "react";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Select from "../../components/Select";
import Skeleton from "../../components/Skeleton";
import TextField from "../../components/TextField";
import { useAdminUsers } from "../../hooks/useAdminUsers";
import { useAuth } from "../../hooks/useAuth";
import type { UserRole } from "../../types/auth";
import { ROLE_OPTIONS } from "../../utils/userLabels";
import { UserRow } from "./UserRow";

// The backend returns every account at once (no paging or search), which is
// fine at a society's size, so searching and filtering happen here. They stay
// in local state rather than the address bar: typing would otherwise add a
// history entry per keystroke.
export function AdminUsers() {
  const { user } = useAuth();
  const { data: users, isPending, isError, isFetching, refetch } = useAdminUsers();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<UserRole | "">("");

  const query = search.trim().toLowerCase();
  const shown = (users ?? []).filter(
    (member) =>
      (!role || member.role === role) &&
      (!query || [member.full_name, member.email, member.department].some((text) => text.toLowerCase().includes(query))),
  );

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Members</h1>
        <p className="mt-1 text-white/60">
          Change roles or deactivate accounts
          {users && ` · ${users.length} ${users.length === 1 ? "member" : "members"}`}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-[2fr_1fr]">
        <TextField
          id="member-search"
          label="Search"
          type="search"
          required={false}
          value={search}
          onChange={setSearch}
          placeholder="Name, email or department"
        />
        <Select
          id="member-role"
          label="Role"
          value={role}
          onChange={setRole}
          options={ROLE_OPTIONS}
          placeholder="All roles"
          required={false}
        />
      </div>

      {isPending && (
        <div aria-busy="true" aria-label="Loading members" className="space-y-3">
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
        </div>
      )}
      {/* Announced as the search narrows the list, instead of the whole list. */}
      {users && (query || role) && (
        <p role="status" className="text-sm text-white/50">
          {shown.length} of {users.length} shown
        </p>
      )}
      {isError && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}
      {users && shown.length === 0 && <EmptyState title="No members found" message="Try another name or role." />}
      {shown.length > 0 && (
        <ul className="space-y-3">
          {shown.map((member) => (
            <li key={member.id}>
              <UserRow member={member} isSelf={member.id === user?.id} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import type { User } from "../../types/auth";

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm font-medium text-sees-mint/80">{label}</dt>
      <dd className="mt-1 whitespace-pre-wrap wrap-anywhere text-white">{value}</dd>
    </div>
  );
}

// level is "" or null when unset (registration sends "" for a blank field).
export function ProfileDetails({ user }: { user: User }) {
  return (
    <dl className="space-y-4">
      <Detail label="Email" value={user.email} />
      <Detail label="Role" value={user.role} />
      <Detail label="Department" value={user.department} />
      <Detail label="Level" value={user.level || "Not set"} />
      <Detail label="Bio" value={user.bio || "No bio yet."} />
      <Detail
        label="Member since"
        value={new Date(user.created_at).toLocaleDateString()}
      />
    </dl>
  );
}

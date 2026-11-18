import { useState } from "react";
import { errorMessage } from "../../api/client";
import Avatar from "../../components/Avatar";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import Select from "../../components/Select";
import { useChangeUserRole } from "../../hooks/useChangeUserRole";
import { useDeactivateUser } from "../../hooks/useDeactivateUser";
import { useToast } from "../../hooks/useToast";
import type { User, UserRole } from "../../types/auth";
import { ROLE_LABELS, ROLE_OPTIONS } from "../../utils/userLabels";

interface UserRowProps {
  member: User;
  // The signed-in admin's own row: no controls, so they can't demote or
  // deactivate themselves (the backend doesn't stop that yet).
  isSelf: boolean;
}

export function UserRow({ member, isSelf }: UserRowProps) {
  const changeRole = useChangeUserRole();
  const deactivate = useDeactivateUser();
  const { showToast } = useToast();
  // The role picked in the dropdown, waiting for confirmation.
  const [pendingRole, setPendingRole] = useState<UserRole | null>(null);
  const [confirmingDeactivate, setConfirmingDeactivate] = useState(false);
  const canManage = !isSelf && member.is_active;

  function confirmRole() {
    if (!pendingRole) return;
    changeRole.mutate(
      { userId: member.id, role: pendingRole },
      {
        onSuccess: () => showToast(`${member.full_name}'s role is now ${ROLE_LABELS[pendingRole]}.`),
        onError: (error) => showToast(errorMessage(error, "Couldn't change the role. Try again."), "error"),
        onSettled: () => setPendingRole(null),
      },
    );
  }

  function confirmDeactivate() {
    deactivate.mutate(member.id, {
      onSuccess: () => showToast(`${member.full_name} can no longer log in.`),
      onError: (error) => showToast(errorMessage(error, "Couldn't deactivate the account. Try again."), "error"),
      onSettled: () => setConfirmingDeactivate(false),
    });
  }

  return (
    <Card as="article" className="flex flex-wrap items-center gap-4">
      <div className="flex min-w-0 flex-1 basis-64 items-center gap-3">
        <Avatar name={member.full_name} imageUrl={member.profile_image_url} size={40} />
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-2 font-medium wrap-anywhere text-white">
            {member.full_name}
            {isSelf && <Badge tone="mint">You</Badge>}
            {!member.is_active && <Badge tone="red">Deactivated</Badge>}
          </p>
          <p className="text-sm wrap-anywhere text-white/50">
            {member.email} · {member.department}
            {member.level && ` · ${member.level}`}
          </p>
        </div>
      </div>

      {canManage ? (
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-40">
            <Select
              id={`role-${member.id}`}
              label="Role"
              value={member.role}
              onChange={(role) => role && role !== member.role && setPendingRole(role)}
              options={ROLE_OPTIONS}
            />
          </div>
          <Button variant="secondary" onClick={() => setConfirmingDeactivate(true)}>
            Deactivate
          </Button>
        </div>
      ) : (
        <Badge>{ROLE_LABELS[member.role]}</Badge>
      )}

      <ConfirmDialog
        open={pendingRole !== null}
        title={`Change ${member.full_name}'s role to ${pendingRole ? ROLE_LABELS[pendingRole] : ""}?`}
        message={
          pendingRole === "ADMIN"
            ? "Admins can approve loans, manage hardware and members, and edit or delete any project."
            : "Their access changes the next time they load a page."
        }
        confirmLabel="Change role"
        tone="primary"
        onConfirm={confirmRole}
        onCancel={() => setPendingRole(null)}
        isPending={changeRole.isPending}
      />
      <ConfirmDialog
        open={confirmingDeactivate}
        title={`Deactivate ${member.full_name}?`}
        message="They won't be able to log in. Their projects and loan history are kept. This can't be undone from the website yet."
        confirmLabel="Deactivate account"
        onConfirm={confirmDeactivate}
        onCancel={() => setConfirmingDeactivate(false)}
        isPending={deactivate.isPending}
      />
    </Card>
  );
}

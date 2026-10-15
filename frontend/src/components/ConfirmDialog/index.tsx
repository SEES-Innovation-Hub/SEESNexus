import type { ReactNode } from "react";
import Button from "../Button";
import Modal from "../Modal";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  // While true the confirm button spins and the dialog can't be dismissed.
  isPending?: boolean;
  // "danger" for anything that deletes or rejects.
  tone?: "primary" | "danger";
}

// "Are you sure?" before an action that can't be undone (delete a project,
// reject a loan, remove a user).
export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
  isPending = false,
  tone = "danger",
}: ConfirmDialogProps) {
  return (
    <Modal
      open={open}
      onClose={onCancel}
      title={title}
      dismissible={!isPending}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel} disabled={isPending}>
            Cancel
          </Button>
          <Button variant={tone} onClick={onConfirm} isLoading={isPending}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div className="text-sm wrap-anywhere text-white/70">{message}</div>
    </Modal>
  );
}

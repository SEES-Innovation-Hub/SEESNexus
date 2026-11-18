import { useState } from "react";
import { errorMessage } from "../../api/client";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import { useRetireHardware } from "../../hooks/useRetireHardware";
import { useToast } from "../../hooks/useToast";
import { useUpdateHardware } from "../../hooks/useUpdateHardware";
import type { Hardware } from "../../types/hardware";
import {
  HARDWARE_CATEGORY_LABELS,
  HARDWARE_STATUS_LABELS,
  HARDWARE_STATUS_TONES,
} from "../../utils/hardwareLabels";

// One inventory item with its admin actions. Retiring is the backend's soft
// delete (status MAINTENANCE, history kept), so it can be undone here.
export function AdminHardwareRow({ item, onEdit }: { item: Hardware; onEdit: () => void }) {
  const retire = useRetireHardware();
  const update = useUpdateHardware();
  const { showToast } = useToast();
  const [confirmingRetire, setConfirmingRetire] = useState(false);
  const isRetired = item.status === "MAINTENANCE";

  function handleRetire() {
    retire.mutate(item.id, {
      onSuccess: () => showToast(`${item.name} is retired. Members can't borrow it.`),
      onError: (error) => showToast(errorMessage(error, "Couldn't retire the item. Try again."), "error"),
      onSettled: () => setConfirmingRetire(false),
    });
  }

  // Back to the status its stock implies: all units out means BORROWED.
  function handleBackInService() {
    update.mutate(
      { id: item.id, payload: { status: item.available_quantity > 0 ? "AVAILABLE" : "BORROWED" } },
      {
        onSuccess: () => showToast(`${item.name} is back in service.`),
        onError: (error) => showToast(errorMessage(error, "Couldn't update the item. Try again."), "error"),
      },
    );
  }

  return (
    <Card as="article" className="flex flex-wrap items-center gap-4">
      <div className="min-w-0 flex-1 basis-64">
        <p className="flex flex-wrap items-center gap-2 font-medium wrap-anywhere text-white">
          {item.name}
          <Badge tone={HARDWARE_STATUS_TONES[item.status]}>{HARDWARE_STATUS_LABELS[item.status]}</Badge>
        </p>
        <p className="text-sm wrap-anywhere text-white/50">
          {HARDWARE_CATEGORY_LABELS[item.category]} · Serial {item.serial_number} ·{" "}
          <span className="text-white/80">
            {item.available_quantity} of {item.quantity} available
          </span>
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" onClick={onEdit}>
          Edit
        </Button>
        {isRetired ? (
          <Button variant="secondary" onClick={handleBackInService} isLoading={update.isPending}>
            Back in service
          </Button>
        ) : (
          <Button variant="secondary" onClick={() => setConfirmingRetire(true)}>
            Retire
          </Button>
        )}
      </div>

      <ConfirmDialog
        open={confirmingRetire}
        title={`Retire ${item.name}?`}
        message="Members won't be able to borrow it. Loans already out are unaffected, its history is kept, and you can put it back in service later."
        confirmLabel="Retire item"
        onConfirm={handleRetire}
        onCancel={() => setConfirmingRetire(false)}
        isPending={retire.isPending}
      />
    </Card>
  );
}

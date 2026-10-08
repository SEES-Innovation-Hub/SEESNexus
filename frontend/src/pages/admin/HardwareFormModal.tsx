import { useState, type FormEvent } from "react";
import { errorMessage } from "../../api/client";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import Select from "../../components/Select";
import TextArea from "../../components/TextArea";
import TextField from "../../components/TextField";
import { useCreateHardware } from "../../hooks/useCreateHardware";
import { useToast } from "../../hooks/useToast";
import { useUpdateHardware } from "../../hooks/useUpdateHardware";
import type { Hardware } from "../../types/hardware";
import { HARDWARE_CATEGORY_OPTIONS } from "../../utils/hardwareLabels";
import {
  DESCRIPTION_MAX,
  EMPTY_HARDWARE,
  NAME_MAX,
  SERIAL_MAX,
  toHardwareFormValues,
  toHardwarePayload,
  unitsOnLoan,
  validateHardware,
  type HardwareFormErrors,
  type HardwareFormValues,
} from "./hardwareFormValues";

// null = adding a new item; a Hardware = editing that one.
export type HardwareFormTarget = Hardware | null;

function HardwareForm({ item, onDone }: { item: HardwareFormTarget; onDone: () => void }) {
  const [values, setValues] = useState<HardwareFormValues>(item ? toHardwareFormValues(item) : EMPTY_HARDWARE);
  const [errors, setErrors] = useState<HardwareFormErrors>({});
  const create = useCreateHardware();
  const update = useUpdateHardware();
  const { showToast } = useToast();
  const save = item ? update : create;
  const onLoan = unitsOnLoan(item);

  function set<K extends keyof HardwareFormValues>(field: K, value: HardwareFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validateHardware(values, onLoan);
    setErrors(found);
    const firstInvalid = Object.keys(found)[0];
    if (firstInvalid) {
      document.getElementById(`hardware-${firstInvalid}`)?.focus();
      return;
    }
    const payload = toHardwarePayload(values);
    const onSuccess = () => {
      showToast(item ? `Saved changes to ${payload.name}.` : `Added ${payload.name} to the inventory.`);
      onDone();
    };
    if (item) update.mutate({ id: item.id, payload }, { onSuccess });
    else create.mutate(payload, { onSuccess });
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <TextField id="hardware-name" label="Name" value={values.name} onChange={(v) => set("name", v)} maxLength={NAME_MAX} error={errors.name} />
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="hardware-serialNumber"
          label="Serial number"
          value={values.serialNumber}
          onChange={(v) => set("serialNumber", v)}
          maxLength={SERIAL_MAX}
          hint="Must be unique."
          error={errors.serialNumber}
        />
        <Select
          id="hardware-category"
          label="Category"
          value={values.category}
          onChange={(v) => set("category", v)}
          options={HARDWARE_CATEGORY_OPTIONS}
          placeholder="Choose a category"
          error={errors.category}
        />
      </div>
      <TextField
        id="hardware-quantity"
        label="How many does the lab own?"
        type="number"
        min={String(Math.max(1, onLoan))}
        value={values.quantity}
        onChange={(v) => set("quantity", v)}
        hint={onLoan > 0 ? `${onLoan} out on loan right now.` : undefined}
        error={errors.quantity}
      />
      <TextArea
        id="hardware-description"
        label="Description"
        rows={3}
        value={values.description}
        onChange={(v) => set("description", v)}
        maxLength={DESCRIPTION_MAX}
        hint="Model, condition, what's in the box."
      />
      {save.error && (
        <p role="alert" className="text-sm wrap-anywhere text-red-400">
          {errorMessage(save.error, "Couldn't save. Try again.")}
        </p>
      )}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onDone} disabled={save.isPending}>
          Cancel
        </Button>
        <Button type="submit" isLoading={save.isPending}>
          {item ? "Save changes" : "Add item"}
        </Button>
      </div>
    </form>
  );
}

// open=false while closed; the form is keyed so each opening starts fresh.
export function HardwareFormModal({ open, item, onClose }: { open: boolean; item: HardwareFormTarget; onClose: () => void }) {
  return (
    <Modal open={open} onClose={onClose} title={item ? `Edit ${item.name}` : "Add hardware"}>
      {open && <HardwareForm key={item?.id ?? "new"} item={item} onDone={onClose} />}
    </Modal>
  );
}

import type { Hardware, HardwareCategory, HardwarePayload } from "../../types/hardware";

// What the add/edit form holds: inputs are strings, category is "" until picked.
export interface HardwareFormValues {
  name: string;
  serialNumber: string;
  category: HardwareCategory | "";
  quantity: string;
  description: string;
  imageUrl: string;
}

export type HardwareFormErrors = Partial<Record<keyof HardwareFormValues, string>>;

// Limits match backend/app/schemas/hardware.py.
export const NAME_MAX = 255;
export const SERIAL_MAX = 255;
export const DESCRIPTION_MAX = 1000;

export const EMPTY_HARDWARE: HardwareFormValues = {
  name: "",
  serialNumber: "",
  category: "",
  quantity: "1",
  description: "",
  imageUrl: "",
};

export function toHardwareFormValues(item: Hardware): HardwareFormValues {
  return {
    name: item.name,
    serialNumber: item.serial_number,
    category: item.category,
    quantity: String(item.quantity),
    description: item.description ?? "",
    imageUrl: item.image_url ?? "",
  };
}

// Units out on loan can't be "un-bought": the backend refuses a quantity below
// them, so the form says so first. 0 for a new item.
export function unitsOnLoan(item: Hardware | null): number {
  return item ? item.quantity - item.available_quantity : 0;
}

export function validateHardware(values: HardwareFormValues, onLoan: number): HardwareFormErrors {
  const quantity = Number(values.quantity);
  const minimum = Math.max(1, onLoan);
  const errors: HardwareFormErrors = {
    name: values.name.trim() ? undefined : "Give the item a name.",
    serialNumber: values.serialNumber.trim() ? undefined : "Enter the serial number on the item or its label.",
    category: values.category ? undefined : "Pick a category.",
    quantity:
      Number.isInteger(quantity) && quantity >= minimum
        ? undefined
        : onLoan > 1
          ? `At least ${onLoan}: that many are out on loan.`
          : "Enter a whole number, 1 or more.",
  };
  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message)) as HardwareFormErrors;
}

// Only call after validateHardware() returned no errors (category is then set).
export function toHardwarePayload(values: HardwareFormValues): HardwarePayload {
  return {
    name: values.name.trim(),
    serial_number: values.serialNumber.trim(),
    category: values.category as HardwareCategory,
    quantity: Number(values.quantity),
    description: values.description.trim() || null,
    image_url: values.imageUrl.trim() || null,
  };
}

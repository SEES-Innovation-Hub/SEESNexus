import type { BadgeTone } from "../components/Badge";
import type { HardwareCategory, HardwareStatus, LoanStatus } from "../types/hardware";

export const HARDWARE_CATEGORY_LABELS: Record<HardwareCategory, string> = {
  MEASUREMENT: "Measurement",
  MICROCONTROLLER: "Microcontroller",
  COMPONENT: "Component",
};

export const HARDWARE_STATUS_LABELS: Record<HardwareStatus, string> = {
  AVAILABLE: "Available",
  BORROWED: "All on loan",
  MAINTENANCE: "Under maintenance",
};

export const HARDWARE_STATUS_TONES: Record<HardwareStatus, BadgeTone> = {
  AVAILABLE: "mint",
  BORROWED: "mustard",
  MAINTENANCE: "red",
};

export const LOAN_STATUS_LABELS: Record<LoanStatus, string> = {
  PENDING: "Waiting for approval",
  APPROVED: "On loan",
  RETURNED: "Returned",
  REJECTED: "Rejected",
};

export const LOAN_STATUS_TONES: Record<LoanStatus, BadgeTone> = {
  PENDING: "mustard",
  APPROVED: "mint",
  RETURNED: "neutral",
  REJECTED: "red",
};

export const HARDWARE_CATEGORY_OPTIONS = Object.entries(HARDWARE_CATEGORY_LABELS).map(
  ([value, label]) => ({ value: value as HardwareCategory, label }),
);

export const HARDWARE_STATUS_OPTIONS = Object.entries(HARDWARE_STATUS_LABELS).map(
  ([value, label]) => ({ value: value as HardwareStatus, label }),
);

// Filters come from the address bar; unknown values mean "no filter".
export function isHardwareCategory(value: string | null): value is HardwareCategory {
  return value !== null && Object.hasOwn(HARDWARE_CATEGORY_LABELS, value);
}

export function isHardwareStatus(value: string | null): value is HardwareStatus {
  return value !== null && Object.hasOwn(HARDWARE_STATUS_LABELS, value);
}

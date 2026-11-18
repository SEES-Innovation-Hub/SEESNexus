// Mirrors backend/app/schemas/hardware.py and models/hardware.py. Keep in sync.
export type HardwareCategory = "MEASUREMENT" | "MICROCONTROLLER" | "COMPONENT";
export type HardwareStatus = "AVAILABLE" | "BORROWED" | "MAINTENANCE";
// CANCELLED: the borrower withdrew the request before an admin decided.
export type LoanStatus = "PENDING" | "APPROVED" | "RETURNED" | "REJECTED" | "CANCELLED";

export interface Hardware {
  id: string;
  name: string;
  description: string | null;
  serial_number: string;
  category: HardwareCategory;
  status: HardwareStatus;
  image_url: string | null;
  quantity: number;
  available_quantity: number;
  added_by_id: string;
}

export interface PaginatedHardware {
  items: Hardware[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// Dates are ISO strings; the ones still in the future are null.
export interface Loan {
  id: string;
  hardware_id: string;
  // The item's name, sent with every loan so lists need no extra lookups.
  hardware_name: string | null;
  borrower_id: string;
  approved_by_id: string | null;
  status: LoanStatus;
  purpose: string;
  request_date: string | null;
  approval_date: string | null;
  expected_return_date: string | null;
  actual_return_date: string | null;
}

// POST /hardware and PUT /hardware/:id (admin). available_quantity is never
// sent: the backend derives it, and moves it with any change to quantity.
export interface HardwarePayload {
  name: string;
  serial_number: string;
  category: HardwareCategory;
  quantity: number;
  description: string | null;
  image_url: string | null;
  status?: HardwareStatus;
}

// POST /hardware/:id/loan (LoanCreateRequest).
export interface LoanRequestPayload {
  purpose: string;
  expected_return_date: string | null;
}

import { api, unwrap } from "./client";
import type {
  Hardware,
  HardwareCategory,
  HardwareStatus,
  Loan,
  LoanRequestPayload,
  PaginatedHardware,
} from "../types/hardware";

// Query parameters GET /hardware accepts (backend/app/api/v1/hardware.py).
export interface HardwareListParams {
  page?: number;
  pageSize?: number;
  category?: HardwareCategory;
  status?: HardwareStatus;
}

// Public endpoint, ordered by name.
export function listHardware({ page, pageSize, category, status }: HardwareListParams = {}) {
  return unwrap<PaginatedHardware>(
    api.get("/hardware", { params: { page, page_size: pageSize, category, status } }),
  );
}

// Public endpoint.
export function getHardware(id: string) {
  return unwrap<Hardware>(api.get(`/hardware/${id}`));
}

// Signed in. Creates a PENDING loan; units only leave the shelf when an admin approves.
export function requestLoan(hardwareId: string, payload: LoanRequestPayload) {
  return unwrap<Loan>(api.post(`/hardware/${hardwareId}/loan`, payload));
}

// Signed in. Every loan of the current user, newest request first.
export function listMyLoans() {
  return unwrap<Loan[]>(api.get("/hardware/loans/my"));
}

// Not used on purpose: PUT /hardware/loans/:id/return lets the BORROWER mark a
// loan returned, so a student could "return" an item they still have. Returns
// are to be confirmed by an admin who has the item in hand, once the backend
// adds that endpoint (DECISIONS open item 20).

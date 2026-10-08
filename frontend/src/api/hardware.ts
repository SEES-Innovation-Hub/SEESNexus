import { api, unwrap } from "./client";
import type {
  Hardware,
  HardwareCategory,
  HardwarePayload,
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

// Admin only. A new item starts with every unit available.
export function createHardware(payload: HardwarePayload) {
  return unwrap<Hardware>(api.post("/hardware", payload));
}

// Admin only. Lowering quantity below the units out on loan is refused (400).
export function updateHardware(id: string, payload: Partial<HardwarePayload>) {
  return unwrap<Hardware>(api.put(`/hardware/${id}`, payload));
}

// Admin only. Soft delete: the item is set to MAINTENANCE and can't be borrowed;
// its loan history is kept. updateHardware with a status puts it back.
export function retireHardware(id: string) {
  return unwrap<Hardware>(api.delete(`/hardware/${id}`));
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

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

// Signed in, ordered by name.
export function listHardware({ page, pageSize, category, status }: HardwareListParams = {}) {
  return unwrap<PaginatedHardware>(
    api.get("/hardware", { params: { page, page_size: pageSize, category, status } }),
  );
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

// Signed in, own loans only. Withdraws a request that is still PENDING; once
// approved the item is out, and only an admin can check it back in.
export function cancelLoanRequest(loanId: string) {
  return unwrap<Loan>(api.put(`/hardware/loans/${loanId}/cancel`));
}

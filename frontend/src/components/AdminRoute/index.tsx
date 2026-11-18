import type { ReactNode } from "react";
import RoleRoute from "../RoleRoute";

// Admin-only pages (/admin/*, and creating or editing events).
export default function AdminRoute({ children }: { children: ReactNode }) {
  return <RoleRoute roles={["ADMIN"]}>{children}</RoleRoute>;
}

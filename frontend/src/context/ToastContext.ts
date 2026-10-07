import { createContext } from "react";

export type ToastTone = "success" | "error";

export interface ToastContextValue {
  // A short message that appears at the bottom of the screen and fades out
  // by itself, e.g. showToast("Project created") or showToast(msg, "error").
  showToast: (message: string, tone?: ToastTone) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);

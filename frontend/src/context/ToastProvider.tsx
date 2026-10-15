import { useCallback, useMemo, useRef, useState, type ReactNode } from "react";
import { ToastContext, type ToastTone } from "./ToastContext";

interface Toast {
  id: number;
  message: string;
  tone: ToastTone;
}

const DISMISS_AFTER_MS = 5000;
const MAX_VISIBLE = 3;

const toneStyles: Record<ToastTone, string> = {
  success: "border-sees-mint/40",
  error: "border-red-400/60",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  // The timer starts in the same call that adds the toast, so no effect is
  // needed. Memoised so components using useToast don't re-render on every toast.
  const showToast = useCallback(
    (message: string, tone: ToastTone = "success") => {
      const id = ++nextId.current;
      setToasts((current) => [...current.slice(-(MAX_VISIBLE - 1)), { id, message, tone }]);
      window.setTimeout(() => dismiss(id), DISMISS_AFTER_MS);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {/* Always in the page (even when empty) so screen readers are already
          watching it when a message arrives; otherwise it isn't announced. */}
      <div
        role="status"
        className="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col items-center gap-2 sm:inset-x-auto sm:right-6 sm:bottom-6 sm:items-end"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex w-full max-w-sm items-center gap-2 rounded-xl border bg-sees-forest py-1 pr-1 pl-4 text-sm text-white shadow-sees-card ${toneStyles[toast.tone]}`}
          >
            <span aria-hidden="true" className={toast.tone === "error" ? "text-red-400" : "text-sees-mint"}>
              {toast.tone === "error" ? "!" : "✓"}
            </span>
            <p className="flex-1 py-2 wrap-anywhere">{toast.message}</p>
            <button
              type="button"
              aria-label="Dismiss"
              onClick={() => dismiss(toast.id)}
              className="inline-flex size-11 shrink-0 items-center justify-center rounded text-lg text-white/60 hover:text-white"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

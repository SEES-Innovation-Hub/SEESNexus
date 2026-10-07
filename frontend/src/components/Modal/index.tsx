import { useId, type ReactNode } from "react";
import { useModalDialog } from "../../hooks/useModalDialog";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  // Action buttons, laid out at the bottom right (stacked on phones).
  footer?: ReactNode;
  // false while a request runs: Esc and clicking outside then do nothing.
  dismissible?: boolean;
}

// Built on the browser's own <dialog>, which already traps keyboard focus inside,
// returns focus to the opening button on close, closes on Esc and sits above
// everything else: no library and no focus-trap code of our own. index.css
// stops the page behind it from scrolling.
export default function Modal({ open, onClose, title, children, footer, dismissible = true }: ModalProps) {
  const dialogRef = useModalDialog(open);
  const titleId = useId();

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      // Esc fires "cancel" first; blocking it keeps the dialog open mid-request.
      onCancel={(event) => {
        event.preventDefault();
        if (dismissible) onClose();
      }}
      // The dialog element itself has no padding, so a click whose target is the
      // dialog (not its content) landed on the backdrop outside the panel.
      onClick={(event) => {
        if (event.target === event.currentTarget && dismissible) onClose();
      }}
      className="m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-lg overflow-y-auto rounded-2xl border border-sees-teal/60 bg-sees-forest p-0 text-white shadow-sees-card backdrop:bg-black/70"
    >
      <div className="space-y-5 p-6">
        <div className="flex items-start justify-between gap-4">
          <h2 id={titleId} className="text-xl font-semibold wrap-anywhere text-sees-mint">
            {title}
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            disabled={!dismissible}
            className="-m-2 inline-flex size-11 shrink-0 items-center justify-center rounded text-2xl leading-none text-white/60 hover:text-white disabled:opacity-40"
          >
            ×
          </button>
        </div>
        <div>{children}</div>
        {footer && <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">{footer}</div>}
      </div>
    </dialog>
  );
}

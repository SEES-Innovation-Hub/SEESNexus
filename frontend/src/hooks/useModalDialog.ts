import { useEffect, useRef } from "react";

// Opens and closes a native <dialog> as a modal from an `open` boolean. Used by
// Modal and the phone sidebar drawer. The browser then handles the focus trap,
// Esc, returning focus and the backdrop.
export function useModalDialog(open: boolean) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  // Opening a modal <dialog> needs the DOM call showModal() (the `open`
  // attribute alone shows it without the backdrop or focus trap), so the
  // `open` prop is synced to the element here: an external DOM API.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return dialogRef;
}

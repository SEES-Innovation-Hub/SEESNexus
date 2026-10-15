// Shared look for every text input, textarea and select. A field with an error
// gets aria-invalid, which turns its border red (the aria-invalid: variant).
export const inputClassName =
  "mt-1 w-full rounded border border-sees-teal bg-sees-void/60 px-3 py-2.5 text-white placeholder:text-white/30 focus:border-sees-mint focus:outline-none focus:ring-1 focus:ring-sees-mint aria-invalid:border-red-400 aria-invalid:focus:ring-red-400";

// Links the input to its hint or error text, so screen readers read it out.
export function describedBy(id: string, { error, hint }: { error?: string; hint?: string }) {
  if (error) return `${id}-error`;
  if (hint) return `${id}-hint`;
  return undefined;
}

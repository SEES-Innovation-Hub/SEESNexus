import type { ReactNode } from "react";

export interface FieldProps {
  id: string;
  label: string;
  error?: string;
  hint?: string;
  optional?: boolean;
}

// Label, the control, then its hint or error. TextField, TextArea and Select use
// this so every form field is laid out and announced the same way.
export default function Field({
  id,
  label,
  error,
  hint,
  optional = false,
  children,
}: FieldProps & { children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-sees-mint/80">
        {label}
        {optional && <span className="font-normal text-white/40"> (optional)</span>}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="mt-1 text-sm wrap-anywhere text-red-400">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-hint`} className="mt-1 text-xs text-white/50">
            {hint}
          </p>
        )
      )}
    </div>
  );
}

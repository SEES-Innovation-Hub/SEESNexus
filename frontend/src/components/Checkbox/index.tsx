interface CheckboxProps {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  hint?: string;
  disabled?: boolean;
}

// A native checkbox with its label beside it. The label is part of the tap
// target, so the whole row is at least 44px high on phones.
export default function Checkbox({ id, label, checked, onChange, hint, disabled }: CheckboxProps) {
  return (
    <div>
      <label htmlFor={id} className="inline-flex min-h-11 cursor-pointer items-center gap-3 text-sm text-white">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
          aria-describedby={hint ? `${id}-hint` : undefined}
          className="size-5 shrink-0 accent-sees-mint"
        />
        {label}
      </label>
      {hint && (
        <p id={`${id}-hint`} className="text-xs text-white/50">
          {hint}
        </p>
      )}
    </div>
  );
}

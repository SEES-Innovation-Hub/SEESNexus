import Field, { type FieldProps } from "../Field";
import { describedBy, inputClassName } from "../Field/fieldStyles";

export interface SelectOption<T extends string> {
  value: T;
  label: string;
}

interface SelectProps<T extends string> extends Omit<FieldProps, "optional"> {
  value: T | "";
  onChange: (value: T | "") => void;
  options: SelectOption<T>[];
  // Shown as a first, empty choice (e.g. "All categories" in a filter).
  placeholder?: string;
  required?: boolean;
}

// A native <select>: keyboard, screen readers and the phone's own picker all
// work for free. scheme-dark makes the opened list dark on Windows/Android too.
export default function Select<T extends string>({
  id,
  label,
  value,
  onChange,
  options,
  placeholder,
  required = true,
  error,
  hint,
}: SelectProps<T>) {
  return (
    <Field id={id} label={label} error={error} hint={hint} optional={!required && !placeholder}>
      <select
        id={id}
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value as T | "")}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, { error, hint })}
        className={`${inputClassName} scheme-dark`}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </Field>
  );
}

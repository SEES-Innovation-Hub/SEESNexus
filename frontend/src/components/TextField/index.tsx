import Field, { type FieldProps } from "../Field";
import { describedBy, inputClassName } from "../Field/fieldStyles";

interface TextFieldProps extends Omit<FieldProps, "optional"> {
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  placeholder?: string;
  autoComplete?: string;
  // For type="date" or "number": the lowest value allowed (YYYY-MM-DD or a number).
  min?: string;
}

// Required by default; required={false} also labels the field "(optional)"
// (except search boxes).
export default function TextField({
  id,
  label,
  value,
  onChange,
  type = "text",
  required = true,
  error,
  hint,
  ...inputProps
}: TextFieldProps) {
  return (
    // A search box is never "optional" the way a form field is, so it isn't labelled so.
    <Field id={id} label={label} error={error} hint={hint} optional={!required && type !== "search"}>
      <input
        id={id}
        type={type}
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, { error, hint })}
        className={inputClassName}
        {...inputProps}
      />
    </Field>
  );
}

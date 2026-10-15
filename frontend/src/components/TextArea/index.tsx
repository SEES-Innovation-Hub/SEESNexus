import Field, { type FieldProps } from "../Field";
import { describedBy, inputClassName } from "../Field/fieldStyles";

interface TextAreaProps extends Omit<FieldProps, "optional"> {
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  required?: boolean;
  maxLength?: number;
  placeholder?: string;
}

// Optional by default (long text is usually a description or bio).
export default function TextArea({
  id,
  label,
  value,
  onChange,
  rows = 4,
  required = false,
  error,
  hint,
  ...textareaProps
}: TextAreaProps) {
  return (
    <Field id={id} label={label} error={error} hint={hint} optional={!required}>
      <textarea
        id={id}
        rows={rows}
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, { error, hint })}
        className={`${inputClassName} resize-y`}
        {...textareaProps}
      />
    </Field>
  );
}

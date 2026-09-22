interface TextFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  type?: string
  required?: boolean
  minLength?: number
}

export default function TextField({ id, label, value, onChange, type = 'text', required = true, minLength }: TextFieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-sees-mint/80">
        {label}
      </label>
      <input
        id={id}
        type={type}
        required={required}
        minLength={minLength}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded border border-sees-teal bg-sees-void/60 px-3 py-2.5 text-white placeholder:text-white/30 focus:border-sees-mint focus:outline-none focus:ring-1 focus:ring-sees-mint"
      />
    </div>
  )
}

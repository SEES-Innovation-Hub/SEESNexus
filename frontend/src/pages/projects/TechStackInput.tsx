import { X } from "lucide-react";
import { useState, type KeyboardEvent } from "react";
import Field from "../../components/Field";
import { inputClassName } from "../../components/Field/fieldStyles";
import { TECH_MAX_ITEMS, TECH_MAX_LENGTH } from "./projectFormValues";

interface TechStackInputProps {
  value: string[];
  onChange: (value: string[]) => void;
}

// Type a technology and press Enter or a comma to turn it into a chip; Backspace
// in the empty box removes the last one. Whatever is still typed when the box
// loses focus is added too, so nothing typed is silently lost on Save.
export function TechStackInput({ value, onChange }: TechStackInputProps) {
  const [draft, setDraft] = useState("");
  const isFull = value.length >= TECH_MAX_ITEMS;

  function addDraft() {
    const tech = draft.trim().replace(/,$/, "").trim();
    setDraft("");
    if (tech && !isFull && !value.includes(tech)) onChange([...value, tech]);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      // Enter would otherwise submit the whole form.
      event.preventDefault();
      addDraft();
    } else if (event.key === "Backspace" && draft === "" && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  }

  return (
    <Field
      id="tech-stack"
      label="Tech stack"
      optional
      hint={isFull ? `That's the maximum of ${TECH_MAX_ITEMS}.` : "Press Enter or a comma after each one."}
    >
      {value.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-x-1">
          {value.map((tech) => (
            <li key={tech} className="max-w-full">
              {/* The button is 44px tall for touch; the visible chip inside is smaller. */}
              <button
                type="button"
                onClick={() => onChange(value.filter((item) => item !== tech))}
                aria-label={`Remove ${tech}`}
                className="group inline-flex min-h-11 max-w-full items-center"
              >
                <span className="inline-flex max-w-full items-center gap-1 rounded-full border border-sees-teal bg-sees-void/60 py-1 pr-2 pl-3 font-mono text-xs text-white/80 group-hover:border-sees-mint">
                  <span className="wrap-anywhere">{tech}</span>
                  <X aria-hidden="true" className="size-3.5 shrink-0 text-white/50" />
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <input
        id="tech-stack"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={addDraft}
        disabled={isFull}
        maxLength={TECH_MAX_LENGTH}
        placeholder="e.g. React, Arduino, Python"
        aria-describedby="tech-stack-hint"
        className={inputClassName}
      />
    </Field>
  );
}

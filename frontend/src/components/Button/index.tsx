import type { ButtonHTMLAttributes } from "react";
import Spinner from "../Spinner";
import { buttonClassName, type ButtonVariant } from "./buttonClassName";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  // Shows a spinner and blocks further clicks while a request runs.
  isLoading?: boolean;
}

// type defaults to "button", not the browser's "submit": a button inside a form
// that isn't meant to submit it (Cancel, Remove) can't send the form by accident.
// Form submit buttons must say type="submit".
export default function Button({
  variant = "primary",
  isLoading = false,
  type = "button",
  disabled,
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      className={buttonClassName(variant, className)}
      {...props}
    >
      {isLoading && <Spinner className="size-4" />}
      {children}
    </button>
  );
}

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

// min-h-11 = 44px, the touch-target size recommended for phones.
const baseStyles =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded px-4 font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sees-mint disabled:cursor-not-allowed disabled:opacity-50";

const variantStyles: Record<ButtonVariant, string> = {
  primary: "bg-sees-mint text-sees-forest hover:shadow-sees-glow",
  secondary: "border border-sees-teal text-sees-mint hover:border-sees-mint",
  ghost: "text-sees-mustard hover:text-sees-mint",
  // Destructive actions only: delete, reject, remove.
  danger: "bg-red-500 text-white hover:bg-red-400",
};

// The button look as a class string, for things that must stay links but should
// look like buttons (e.g. a "Register" link): <PrefetchLink className={buttonClassName()} />.
export function buttonClassName(variant: ButtonVariant = "primary", extra = "") {
  return `${baseStyles} ${variantStyles[variant]} ${extra}`.trim();
}

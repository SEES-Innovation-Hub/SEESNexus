export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "md" | "lg";

// Hover effects use not-disabled:hover so a disabled button doesn't react to the
// mouse (and links, which are never disabled, still do).
// A loading button (aria-busy) is also disabled, but keeps its full colour: it is
// busy, not unavailable. Only a truly disabled one turns grey (not-aria-busy).
const baseStyles =
  "inline-flex items-center justify-center gap-2 rounded font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sees-mint disabled:cursor-not-allowed aria-busy:cursor-wait";

// md: min-h-11 = 44px, the touch-target size recommended for phones.
// lg: the bigger call-to-action buttons on Landing.
const sizeStyles: Record<ButtonSize, string> = {
  md: "min-h-11 px-4",
  lg: "min-h-12 px-6",
};

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-sees-mint text-sees-forest not-disabled:hover:shadow-sees-glow disabled:not-aria-busy:bg-white/10 disabled:not-aria-busy:text-white/40",
  secondary:
    "border border-sees-teal text-sees-mint not-disabled:hover:border-sees-mint disabled:not-aria-busy:border-white/10 disabled:not-aria-busy:text-white/35",
  ghost: "text-sees-mustard not-disabled:hover:text-sees-mint disabled:not-aria-busy:text-white/35",
  // Destructive actions only: delete, reject, remove. A deep red, so it reads as
  // serious without shouting over the mint and mustard brand colours.
  danger:
    "bg-red-700 text-white not-disabled:hover:bg-red-600 disabled:not-aria-busy:bg-white/10 disabled:not-aria-busy:text-white/40",
};

// The button look as a class string, for things that must stay links but should
// look like buttons (e.g. a "Register" link): <PrefetchLink className={buttonClassName()} />.
export function buttonClassName(variant: ButtonVariant = "primary", extra = "", size: ButtonSize = "md") {
  return `${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${extra}`.trim();
}

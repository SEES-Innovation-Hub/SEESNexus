// A small spinning ring in the current text colour. Decorative: whatever shows
// it must also say what is happening (button text, aria-busy, a status line).
export default function Spinner({ className = "size-5" }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block shrink-0 animate-spin rounded-full border-2 border-current border-r-transparent ${className}`}
    />
  );
}

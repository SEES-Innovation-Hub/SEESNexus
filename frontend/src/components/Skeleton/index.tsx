// A pulsing placeholder in the shape of content that is still loading. Size it
// with className (e.g. "h-6 w-40"). Hidden from screen readers; the area that
// is loading should announce it instead (aria-busy on the region).
// The pulse stops for visitors who asked their device for reduced motion.
export default function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded bg-sees-mint/10 motion-reduce:animate-none ${className}`}
    />
  );
}

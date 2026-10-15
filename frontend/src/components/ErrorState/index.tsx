import Button from "../Button";

interface ErrorStateProps {
  message?: string;
  // Usually the query's refetch; omit it to hide the button.
  onRetry?: () => void;
  isRetrying?: boolean;
}

// What a page or list shows when its data couldn't be loaded.
export default function ErrorState({
  message = "Couldn't load this right now. Check your connection and try again.",
  onRetry,
  isRetrying = false,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-4 rounded-2xl border border-red-400/30 px-6 py-12 text-center"
    >
      <p className="max-w-md text-sm wrap-anywhere text-white/70">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry} isLoading={isRetrying}>
          Try again
        </Button>
      )}
    </div>
  );
}

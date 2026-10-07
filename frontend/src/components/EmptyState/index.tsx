import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  message?: string;
  // Usually a button or link to create the first item.
  action?: ReactNode;
}

// What a list shows when it loaded fine but has nothing in it.
export default function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-sees-teal px-6 py-12 text-center">
      <p className="text-lg font-medium text-sees-mint">{title}</p>
      {message && <p className="max-w-md text-sm text-white/60">{message}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

import Button from "../Button";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

// On the narrowest phones (under 360px) the buttons show only their arrows, or
// the row would be wider than the screen; the aria-labels still say what they do.
const wordClassName = "hidden min-[360px]:inline";

// Previous / "Page 2 of 5" / Next. Pages come from the backend's paginated
// responses ({items, page, page_size, total, total_pages}). Hidden for one page.
export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <nav aria-label="Pagination" className="flex items-center justify-between gap-3">
      <Button
        variant="secondary"
        aria-label="Previous page"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        <span aria-hidden="true">←</span>
        <span aria-hidden="true" className={wordClassName}>
          Previous
        </span>
      </Button>
      <p aria-live="polite" className="text-sm whitespace-nowrap text-white/60">
        Page {page} of {totalPages}
      </p>
      <Button
        variant="secondary"
        aria-label="Next page"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        <span aria-hidden="true" className={wordClassName}>
          Next
        </span>
        <span aria-hidden="true">→</span>
      </Button>
    </nav>
  );
}

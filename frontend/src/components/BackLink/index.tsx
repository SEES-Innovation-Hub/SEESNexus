import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
import PrefetchLink from "../PrefetchLink";

// "← All projects" above a detail page. Full-size text in the brand mint, so it
// reads as navigation rather than a footnote, with a 44px tap area.
export default function BackLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <PrefetchLink
      to={to}
      className="group inline-flex min-h-11 items-center gap-2 font-medium text-sees-mint/80 transition hover:text-sees-mint"
    >
      <ArrowLeft aria-hidden="true" className="size-5 transition group-hover:-translate-x-0.5" />
      {children}
    </PrefetchLink>
  );
}

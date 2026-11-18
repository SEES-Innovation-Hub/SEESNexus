import { ArrowRight } from "lucide-react";
import type { ReactNode } from "react";
import PrefetchLink from "../PrefetchLink";

// "All events →" beside a section heading, leading to the full page.
export default function SeeAllLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <PrefetchLink
      to={to}
      className="group inline-flex min-h-11 items-center gap-1.5 font-medium text-sees-mint/80 transition hover:text-sees-mint"
    >
      {children}
      <ArrowRight aria-hidden="true" className="size-4 transition group-hover:translate-x-0.5" />
    </PrefetchLink>
  );
}

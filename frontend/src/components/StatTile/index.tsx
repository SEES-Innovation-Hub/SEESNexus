import type { ReactNode } from "react";
import PrefetchLink from "../PrefetchLink";

interface StatTileProps {
  label: string;
  value: number;
  // A short line under the number, e.g. "12 active".
  detail?: ReactNode;
  // Makes the whole tile a link to the page behind the number.
  to?: string;
}

// One headline number (dataviz "stat tile": sentence-case label, a semibold
// compact value, text in text colours rather than the accent). Numbers come
// straight from the API; nothing here is ever hardcoded.
export default function StatTile({ label, value, detail, to }: StatTileProps) {
  const content = (
    <>
      <p className="text-sm text-white/60">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-white tabular-nums">
        {new Intl.NumberFormat(undefined, { notation: "compact" }).format(value)}
      </p>
      {detail && <p className="mt-1 text-sm text-white/50">{detail}</p>}
    </>
  );
  const className = "block h-full rounded-2xl border border-sees-teal/40 bg-gradient-card p-5 shadow-sees-card";

  return to ? (
    <PrefetchLink
      to={to}
      className={`${className} transition-colors hover:border-sees-mint/50 focus-visible:outline-2 focus-visible:outline-sees-mint`}
    >
      {content}
    </PrefetchLink>
  ) : (
    <div className={className}>{content}</div>
  );
}

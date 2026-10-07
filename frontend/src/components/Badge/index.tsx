import type { ReactNode } from "react";

export type BadgeTone = "mint" | "mustard" | "red" | "neutral";

const toneStyles: Record<BadgeTone, string> = {
  mint: "border-sees-mint/40 text-sees-mint",
  mustard: "border-sees-mustard/40 text-sees-mustard",
  red: "border-red-400/40 text-red-300",
  neutral: "border-white/20 text-white/70",
};

// A small rounded label for a status or category ("In progress", "Approved").
// Each feature maps its own values to a tone, next to its label map in utils/.
export default function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap ${toneStyles[tone]}`}
    >
      {children}
    </span>
  );
}

import type { HTMLAttributes } from "react";

type CardPadding = "none" | "md" | "lg";

interface CardProps extends HTMLAttributes<HTMLElement> {
  // Pick the element that fits the content: an <article> for a project or item,
  // a <section> for a titled block, an <li> inside a list.
  as?: "div" | "article" | "section" | "li";
  padding?: CardPadding;
}

const paddingStyles: Record<CardPadding, string> = {
  none: "",
  md: "p-5",
  lg: "p-6 sm:p-8",
};

// The glass panel used across the app (Login box, project cards, admin panels).
export default function Card({ as: Tag = "div", padding = "md", className = "", ...props }: CardProps) {
  return (
    <Tag
      className={`rounded-2xl border border-sees-teal/40 bg-gradient-card shadow-sees-card ${paddingStyles[padding]} ${className}`}
      {...props}
    />
  );
}

import type { ReactNode } from "react";
import { isHttpUrl } from "../../utils/isHttpUrl";

// A small Markdown renderer for article bodies. It builds React elements and
// never sets innerHTML, so whatever an author types can't inject markup or
// scripts; links are only made for http(s) addresses.
//
// Supported: # / ## / ### headings, paragraphs, - or * bullet lists, 1. numbered
// lists, > quotes, ``` code blocks, **bold**, *italic*, `code` and [text](https://…).

const INLINE = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g;

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  return text.split(INLINE).map((part, index) => {
    const key = `${keyPrefix}-${index}`;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={key} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return <code key={key} className="rounded bg-sees-void/60 px-1.5 py-0.5 font-mono text-sm text-sees-mint">{part.slice(1, -1)}</code>;
    }
    const link = /^\[([^\]]+)\]\(([^)\s]+)\)$/.exec(part);
    if (link) {
      const [, label, href] = link;
      return isHttpUrl(href) ? (
        <a key={key} href={href} target="_blank" rel="noreferrer" className="text-sees-mustard underline hover:text-sees-mint">
          {label}
        </a>
      ) : (
        label
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={key}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

export default function Markdown({ source }: { source: string }) {
  const lines = source.replace(/\r\n?/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const key = `b${blocks.length}`;

    if (line.trim() === "") {
      i++;
      continue;
    }

    if (line.startsWith("```")) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) code.push(lines[i++]);
      i++; // the closing fence (or the end of the text)
      blocks.push(
        <pre key={key} className="overflow-x-auto rounded-lg bg-sees-void/70 p-4 font-mono text-sm text-white/80">
          <code>{code.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      const content = renderInline(heading[2], key);
      blocks.push(
        level === 1 ? (
          <h2 key={key} className="pt-2 text-2xl font-semibold text-white">{content}</h2>
        ) : level === 2 ? (
          <h3 key={key} className="pt-2 text-xl font-semibold text-white">{content}</h3>
        ) : (
          <h4 key={key} className="pt-1 text-lg font-medium text-sees-mint">{content}</h4>
        ),
      );
      i++;
      continue;
    }

    if (/^\s*[-*]\s+/.test(line) || /^\s*\d+[.)]\s+/.test(line)) {
      const ordered = /^\s*\d+[.)]\s+/.test(line);
      const pattern = ordered ? /^\s*\d+[.)]\s+/ : /^\s*[-*]\s+/;
      const items: ReactNode[] = [];
      while (i < lines.length && pattern.test(lines[i])) {
        items.push(<li key={`${key}-${items.length}`}>{renderInline(lines[i].replace(pattern, ""), `${key}-${items.length}`)}</li>);
        i++;
      }
      blocks.push(
        ordered ? (
          <ol key={key} className="list-decimal space-y-1 pl-6">{items}</ol>
        ) : (
          <ul key={key} className="list-disc space-y-1 pl-6">{items}</ul>
        ),
      );
      continue;
    }

    if (line.startsWith(">")) {
      const quote: string[] = [];
      while (i < lines.length && lines[i].startsWith(">")) quote.push(lines[i++].replace(/^>\s?/, ""));
      blocks.push(
        <blockquote key={key} className="border-l-2 border-sees-mustard pl-4 text-white/70 italic">
          {renderInline(quote.join(" "), key)}
        </blockquote>,
      );
      continue;
    }

    // A paragraph runs until a blank line or the start of another block.
    const paragraph: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^(#{1,3}\s|```|>|\s*[-*]\s+|\s*\d+[.)]\s+)/.test(lines[i])
    ) {
      paragraph.push(lines[i++]);
    }
    blocks.push(
      <p key={key} className="wrap-anywhere">
        {renderInline(paragraph.join(" "), key)}
      </p>,
    );
  }

  return <div className="space-y-4 leading-relaxed text-white/80">{blocks}</div>;
}

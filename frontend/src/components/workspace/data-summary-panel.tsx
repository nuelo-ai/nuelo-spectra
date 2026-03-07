"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { CollectionFile } from "@/types/workspace";

interface DataSummaryPanelProps {
  file: CollectionFile | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DataSummaryPanel({
  file,
  open,
  onOpenChange,
}: DataSummaryPanelProps) {
  const summary = file?.data_summary;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{file?.filename || "File Information"}</SheetTitle>
        </SheetHeader>

        <div className="space-y-4 py-4">
          {summary ? (
            <div>
              <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
                Data Summary
              </h3>
              <div className="bg-accent/50 p-4 rounded-lg">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <MarkdownContent content={summary} />
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No data summary available for this file.
            </p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

/**
 * Simple markdown renderer for data summaries.
 * Renders headings, bold, lists, tables, code.
 */
function MarkdownContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("### ")) {
      elements.push(
        <h4 key={i} className="text-sm font-semibold mt-4 mb-2">
          {line.slice(4)}
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h3 key={i} className="text-base font-semibold mt-5 mb-2">
          {line.slice(3)}
        </h3>
      );
      i++;
      continue;
    }

    // Table
    if (line.includes("|") && lines[i + 1]?.includes("---")) {
      const headers = line
        .split("|")
        .map((c) => c.trim())
        .filter(Boolean);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes("|")) {
        rows.push(
          lines[i]
            .split("|")
            .map((c) => c.trim())
            .filter(Boolean)
        );
        i++;
      }
      elements.push(
        <div key={`table-${i}`} className="overflow-x-auto my-3">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                {headers.map((h, j) => (
                  <th
                    key={j}
                    className="text-left py-2 px-3 text-xs font-semibold text-muted-foreground"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, ri) => (
                <tr key={ri} className="border-b border-border/50">
                  {row.map((cell, ci) => (
                    <td key={ci} className="py-2 px-3 text-sm">
                      {formatInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // Ordered list
    if (/^\d+\.\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s/, ""));
        i++;
      }
      elements.push(
        <ol
          key={`ol-${i}`}
          className="list-decimal list-inside space-y-1.5 my-2"
        >
          {items.map((item, j) => (
            <li key={j} className="text-sm leading-relaxed">
              {formatInline(item)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Unordered list
    if (line.startsWith("- ")) {
      const items: string[] = [];
      while (i < lines.length && lines[i].startsWith("- ")) {
        items.push(lines[i].slice(2));
        i++;
      }
      elements.push(
        <ul
          key={`ul-${i}`}
          className="list-disc list-inside space-y-1.5 my-2"
        >
          {items.map((item, j) => (
            <li key={j} className="text-sm leading-relaxed">
              {formatInline(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    if (line.trim()) {
      elements.push(
        <p key={i} className="text-sm leading-relaxed my-1.5">
          {formatInline(line)}
        </p>
      );
    }

    i++;
  }

  return <>{elements}</>;
}

function formatInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

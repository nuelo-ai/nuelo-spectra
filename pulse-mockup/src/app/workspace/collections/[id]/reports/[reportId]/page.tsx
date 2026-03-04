"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MOCK_REPORTS } from "@/lib/mock-data";

export default function ReportReaderPage() {
  const params = useParams();
  const id = params.id as string;
  const reportId = params.reportId as string;

  const report =
    MOCK_REPORTS.find((r) => r.id === reportId) ?? MOCK_REPORTS[0];

  const handleDownloadMarkdown = () => {
    const blob = new Blob([report.markdownContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.title.replace(/\s+/g, "-").toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative min-h-screen">
      {/* Sticky header bar */}
      <div className="sticky top-0 z-30 flex items-center justify-between px-6 py-3 bg-[#111827] border-b border-[#1e293b] backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link href={`/workspace/collections/${id}`}>
            <Button variant="ghost" size="sm" className="gap-1.5">
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
          </Link>
          <div className="h-4 w-px bg-border" />
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium truncate max-w-xs">
            {report.title}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={handleDownloadMarkdown}
          >
            <Download className="h-3.5 w-3.5" /> Download as Markdown
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 opacity-60 cursor-not-allowed"
            disabled
          >
            <Download className="h-3.5 w-3.5" /> Download as PDF
          </Button>
        </div>
      </div>

      {/* Document paper area */}
      <div className="flex justify-center py-10 px-4 bg-[#0a0e1a] min-h-screen">
        <div className="w-full max-w-3xl bg-white rounded-lg shadow-2xl shadow-black/40 px-16 py-12 text-gray-900">
          {/* Report metadata header within the paper */}
          <div className="mb-8 pb-6 border-b border-gray-200">
            <Badge className="mb-3 bg-blue-100 text-blue-700 border-0 text-xs">
              {report.type}
            </Badge>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {report.title}
            </h1>
            <p className="text-sm text-gray-500">
              Generated {report.generatedAt}
            </p>
          </div>
          {/* Markdown content */}
          <div className="prose prose-slate max-w-none">
            <div
              dangerouslySetInnerHTML={{
                __html: convertMarkdownToHtml(report.markdownContent),
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Converts a markdown string to an HTML string.
 * Handles: headings (h1-h3), bold, italic, horizontal rules,
 * unordered lists, fenced tables, and paragraph text.
 */
function convertMarkdownToHtml(markdown: string): string {
  const lines = markdown.split("\n");
  const htmlParts: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Heading 1
    if (line.startsWith("# ")) {
      htmlParts.push(
        `<h1>${applyInlineStyles(line.slice(2).trim())}</h1>`
      );
      i++;
      continue;
    }

    // Heading 2
    if (line.startsWith("## ")) {
      htmlParts.push(
        `<h2>${applyInlineStyles(line.slice(3).trim())}</h2>`
      );
      i++;
      continue;
    }

    // Heading 3
    if (line.startsWith("### ")) {
      htmlParts.push(
        `<h3>${applyInlineStyles(line.slice(4).trim())}</h3>`
      );
      i++;
      continue;
    }

    // Horizontal rule
    if (line.trim() === "---") {
      htmlParts.push("<hr />");
      i++;
      continue;
    }

    // Table (lines starting with |)
    if (line.trim().startsWith("|")) {
      const tableRows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const row = lines[i];
        // Skip separator rows like |---|---|
        if (/^\s*\|[\s\-|:]+\|\s*$/.test(row)) {
          i++;
          continue;
        }
        const cells = row
          .trim()
          .replace(/^\|/, "")
          .replace(/\|$/, "")
          .split("|")
          .map((cell) => cell.trim());
        tableRows.push(cells);
        i++;
      }

      if (tableRows.length === 0) continue;

      let tableHtml = "<table>";
      // First row is thead
      tableHtml += "<thead><tr>";
      for (const cell of tableRows[0]) {
        tableHtml += `<th>${applyInlineStyles(cell)}</th>`;
      }
      tableHtml += "</tr></thead>";
      // Remaining rows are tbody
      if (tableRows.length > 1) {
        tableHtml += "<tbody>";
        for (const row of tableRows.slice(1)) {
          tableHtml += "<tr>";
          for (const cell of row) {
            tableHtml += `<td>${applyInlineStyles(cell)}</td>`;
          }
          tableHtml += "</tr>";
        }
        tableHtml += "</tbody>";
      }
      tableHtml += "</table>";
      htmlParts.push(tableHtml);
      continue;
    }

    // Unordered list
    if (line.startsWith("- ")) {
      let listHtml = "<ul>";
      while (i < lines.length && lines[i].startsWith("- ")) {
        listHtml += `<li>${applyInlineStyles(lines[i].slice(2).trim())}</li>`;
        i++;
      }
      listHtml += "</ul>";
      htmlParts.push(listHtml);
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      htmlParts.push(
        `<blockquote>${applyInlineStyles(line.slice(2).trim())}</blockquote>`
      );
      i++;
      continue;
    }

    // Empty line — skip
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Default: paragraph
    htmlParts.push(`<p>${applyInlineStyles(line.trim())}</p>`);
    i++;
  }

  return htmlParts.join("\n");
}

/**
 * Applies inline markdown styles: bold (**text**), italic (*text*),
 * and inline code (`code`).
 */
function applyInlineStyles(text: string): string {
  // Bold+italic: ***text***
  text = text.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  // Bold: **text**
  text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Italic: *text*
  text = text.replace(/\*(.+?)\*/g, "<em>$1</em>");
  // Inline code: `code`
  text = text.replace(/`(.+?)`/g, "<code>$1</code>");
  return text;
}

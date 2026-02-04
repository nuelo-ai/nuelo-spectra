"use client";

import { Button } from "@/components/ui/button";
import { Download, FileText } from "lucide-react";
import Papa from "papaparse";

interface CSVDownloadButtonProps {
  data: {
    columns: string[];
    rows: Record<string, any>[];
  };
  filename?: string;
}

/**
 * CSV Download Button
 * Converts table data to CSV using papaparse and triggers download.
 */
export function CSVDownloadButton({ data, filename }: CSVDownloadButtonProps) {
  const handleDownload = () => {
    if (!data || !data.columns || !data.rows || data.rows.length === 0) {
      return;
    }

    // Convert data to CSV using papaparse
    const csv = Papa.unparse({
      fields: data.columns,
      data: data.rows.map((row) => data.columns.map((col) => row[col] ?? "")),
    });

    // Create blob and download
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download =
      filename || `spectra-export-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const isDisabled = !data || !data.rows || data.rows.length === 0;

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleDownload}
      disabled={isDisabled}
      className="gap-2"
    >
      <Download className="h-4 w-4" />
      Download CSV
    </Button>
  );
}

interface MarkdownDownloadButtonProps {
  queryBrief: string;
  explanation: string;
  tableData?: {
    columns: string[];
    rows: Record<string, any>[];
  };
  filename?: string;
}

/**
 * Markdown Download Button
 * Generates a formatted Markdown report and triggers download.
 */
export function MarkdownDownloadButton({
  queryBrief,
  explanation,
  tableData,
  filename,
}: MarkdownDownloadButtonProps) {
  const handleDownload = () => {
    // Generate Markdown content
    let markdown = `# ${queryBrief}\n\n`;
    markdown += `## Analysis\n\n${explanation}\n\n`;

    // Add table data if available
    if (tableData && tableData.columns && tableData.rows && tableData.rows.length > 0) {
      markdown += `## Data\n\n`;

      // Create markdown table header
      markdown += `| ${tableData.columns.join(" | ")} |\n`;
      markdown += `| ${tableData.columns.map(() => "---").join(" | ")} |\n`;

      // Add rows
      tableData.rows.forEach((row) => {
        const rowValues = tableData.columns.map((col) => {
          const value = row[col];
          // Escape pipe characters and handle null/undefined
          return value != null ? String(value).replace(/\|/g, "\\|") : "";
        });
        markdown += `| ${rowValues.join(" | ")} |\n`;
      });
    }

    // Create blob and download
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download =
      filename ||
      `spectra-analysis-${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Button variant="outline" size="sm" onClick={handleDownload} className="gap-2">
      <FileText className="h-4 w-4" />
      Download Markdown
    </Button>
  );
}

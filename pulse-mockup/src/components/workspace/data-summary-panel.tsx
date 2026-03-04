"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { FileItem } from "@/lib/mock-data";

// --- Mock AI analysis content (simulates backend data_summary markdown) ---

const MOCK_DATA_SUMMARY = `## Dataset Overview

This file contains **12,847 transactional records** across **24 columns**, spanning Q3 2025. The data covers sales transactions with geographic, temporal, and categorical dimensions.

### Column Schema

| Column | Type | Description |
|--------|------|-------------|
| transaction_id | text | Unique transaction identifier |
| amount | numeric | Transaction value in USD |
| category | categorical | Product category (12 unique values) |
| created_at | datetime | Transaction timestamp |
| region | categorical | Geographic region (5 regions) |
| quantity | numeric | Units sold per transaction |

### Data Types Detected

- **Numeric**: amount, quantity, discount_pct, tax_amount (4 columns)
- **Categorical**: category, region, status, payment_method (6 columns)
- **Datetime**: created_at, updated_at, shipped_at (3 columns)
- **Text**: transaction_id, notes, customer_id (3 columns)
- **Other**: 8 additional columns

### Key Findings

1. **68% of transactions cluster in Mon–Wed**, suggesting weekly cyclicality in purchasing behavior
2. **Amount distribution is right-skewed** with outliers above $12,000 — top 5% of transactions account for 31% of total revenue
3. **Revenue concentration in 3 regions** (North, West, Central) makes up 82% of volume, suggesting geographic dependency risk
4. **Missing values in 'region' column (2.3%)** correlate with bulk-import records from legacy system migration

### Data Quality

- **Quality Score: 87/100**
- 2.3% missing values in \`region\` column
- 12 duplicate \`transaction_id\` entries detected
- 3 records with negative \`amount\` values (possible refunds or data errors)

### Suggested Analyses

- **Anomaly detection** on amount time series to flag unusual spikes
- **Category-based segmentation** to identify high-value product groups
- **Regional trend comparison** across quarters for geographic strategy`;

const MOCK_USER_CONTEXT =
  "This is our Q3 revenue data exported from Salesforce. The 'status' column values mean: 1=Completed, 2=Pending, 3=Cancelled. Negative amounts are refunds.";

interface DataSummaryPanelProps {
  file: FileItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DataSummaryPanel({
  file,
  open,
  onOpenChange,
}: DataSummaryPanelProps) {
  const [feedbackInput, setFeedbackInput] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleSubmitFeedback = () => {
    if (!feedbackInput.trim()) return;
    setFeedbackInput("");
    setSubmitSuccess(true);
    setTimeout(() => setSubmitSuccess(false), 3000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{file?.name || "File Information"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* AI Analysis Section */}
          <div>
            <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
              AI Analysis
            </h3>
            <div className="bg-accent/50 p-4 rounded-lg">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <MarkdownContent content={MOCK_DATA_SUMMARY} />
              </div>
            </div>
          </div>

          {/* User Context Section */}
          <div>
            <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
              Your Context
            </h3>
            <p className="text-sm bg-accent/30 p-4 rounded-lg">
              {MOCK_USER_CONTEXT}
            </p>
          </div>

          {/* Refine AI Understanding */}
          <div className="border-t pt-4">
            <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
              Refine AI Understanding
            </h3>
            <p className="text-xs text-muted-foreground mb-2">
              Provide additional context to improve how the AI interprets your
              data.
            </p>
            <textarea
              value={feedbackInput}
              onChange={(e) => setFeedbackInput(e.target.value)}
              placeholder="e.g., The 'status' column values mean: 1=Active, 2=Inactive, 3=Pending..."
              className="w-full min-h-[80px] rounded-lg border border-border bg-background p-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
              rows={3}
            />
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleSubmitFeedback}
                disabled={!feedbackInput.trim()}
                className="bg-primary text-primary-foreground rounded py-1.5 px-4 text-sm hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save Feedback
              </button>
              {submitSuccess && (
                <span className="text-sm text-green-600">Saved!</span>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Simple markdown renderer for mockup — renders headings, bold, lists, tables, code.
 * Avoids adding react-markdown dependency to the mockup app.
 */
function MarkdownContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Headings
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
      i += 2; // skip header + separator
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
        <ol key={`ol-${i}`} className="list-decimal list-inside space-y-1.5 my-2">
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
        <ul key={`ul-${i}`} className="list-disc list-inside space-y-1.5 my-2">
          {items.map((item, j) => (
            <li key={j} className="text-sm leading-relaxed">
              {formatInline(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Paragraph (non-empty lines)
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

/** Renders inline markdown: **bold** and `code` */
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

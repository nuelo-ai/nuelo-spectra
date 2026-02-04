"use client";

import { useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/data/DataTable";
import { TypingIndicator } from "./TypingIndicator";
import { ChevronDown } from "lucide-react";

interface DataCardProps {
  queryBrief?: string; // Section 1: user's query summary
  tableData?: {
    // Section 2: data table
    columns: string[];
    rows: Record<string, any>[];
  };
  explanation?: string; // Section 3: AI explanation
  generatedCode?: string; // Code for code display (Plan 06)
  isStreaming?: boolean; // Whether this card is still receiving data
  isCollapsed?: boolean; // Whether card starts collapsed (older cards)
  onToggleCollapse?: () => void; // Callback for collapse toggle
}

/**
 * Data Card component with progressive rendering.
 * Shows Query Brief -> Data Table -> AI Explanation in sequence.
 * Supports collapse/expand for older cards.
 */
export function DataCard({
  queryBrief,
  tableData,
  explanation,
  generatedCode,
  isStreaming = false,
  isCollapsed = false,
  onToggleCollapse,
}: DataCardProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(isCollapsed);

  const collapsed = onToggleCollapse ? isCollapsed : internalCollapsed;
  const toggleCollapse = onToggleCollapse || (() => setInternalCollapsed(!internalCollapsed));

  // Parse execution_result if it's a JSON string with tabular data
  const parseTableData = (result: any) => {
    if (!result) return null;

    // If result is already structured
    if (result.columns && result.rows) {
      return { columns: result.columns, rows: result.rows };
    }

    // If result is a string, try to parse it
    if (typeof result === "string") {
      try {
        const parsed = JSON.parse(result);
        if (parsed.columns && parsed.rows) {
          return { columns: parsed.columns, rows: parsed.rows };
        }
      } catch {
        // Not JSON, ignore
      }
    }

    return null;
  };

  const displayTableData = tableData || parseTableData(tableData);

  return (
    <Collapsible
      open={!collapsed}
      onOpenChange={toggleCollapse}
      className="rounded-lg border bg-card shadow-sm"
    >
      {/* Section 1: Query Brief (always visible in header) */}
      <CollapsibleTrigger className="w-full px-6 py-4 flex items-start gap-3 hover:bg-muted/50 transition-colors">
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="secondary" className="text-xs">
              Data Card
            </Badge>
          </div>
          <h3 className="font-medium text-sm">{queryBrief || "Query in progress..."}</h3>
        </div>
        <ChevronDown
          className={`h-5 w-5 text-muted-foreground shrink-0 transition-transform ${
            collapsed ? "-rotate-90" : ""
          }`}
        />
      </CollapsibleTrigger>

      {/* Section 2 & 3: Data Table and AI Explanation */}
      <CollapsibleContent className="px-6 pb-6 space-y-6">
        {/* Section 2: Data Table */}
        {displayTableData ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Data Results</h4>
            <DataTable columns={displayTableData.columns} data={displayTableData.rows} />
          </div>
        ) : isStreaming ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Data Results</h4>
            <div className="flex items-center justify-center p-8 border rounded-lg bg-muted/20">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                Loading data...
              </div>
            </div>
          </div>
        ) : null}

        {/* Download buttons placeholder (Plan 06) */}
        {/* Download buttons added by Plan 06 */}

        {/* Code display placeholder (Plan 06) */}
        {/* Code display added by Plan 06 */}

        {/* Section 3: AI Explanation */}
        {explanation ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Analysis</h4>
            <div className="rounded-lg bg-muted/30 p-4">
              <p className="text-sm whitespace-pre-wrap break-words">{explanation}</p>
            </div>
          </div>
        ) : isStreaming ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Analysis</h4>
            <div className="rounded-lg bg-muted/30 p-4">
              <TypingIndicator />
            </div>
          </div>
        ) : null}
      </CollapsibleContent>
    </Collapsible>
  );
}

"use client";

import { useState, useRef } from "react";
import dynamic from "next/dynamic";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/data/DataTable";
import { TypingIndicator } from "./TypingIndicator";
import { ChevronDown, ExternalLink } from "lucide-react";
import { CSVDownloadButton, MarkdownDownloadButton } from "@/components/data/DownloadButtons";
import { CodeDisplay } from "@/components/data/CodeDisplay";
import ChartSkeleton from "@/components/chart/ChartSkeleton";
import ChartErrorAlert from "@/components/chart/ChartErrorAlert";
import { ChartExportButtons } from "@/components/chart/ChartExportButtons";
import type { ChartRendererHandle } from "@/components/chart/ChartRenderer";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const ChartRenderer = dynamic(
  () => import("@/components/chart/ChartRenderer"),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

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
  followUpSuggestions?: string[]; // Follow-up query suggestions
  onFollowUpClick?: (suggestion: string) => void; // Callback when follow-up chip clicked
  searchSources?: { title: string; url: string }[]; // Web search source citations
  chartSpecs?: string; // JSON string from backend (fig.to_json())
  chartError?: string; // Error message if chart generation failed
  visualizationInProgress?: boolean; // True during chart generation
  visualizationStage?: string; // Current stage message for skeleton
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
  followUpSuggestions,
  onFollowUpClick,
  searchSources,
  chartSpecs,
  chartError,
  visualizationInProgress,
  visualizationStage,
}: DataCardProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(isCollapsed);
  const chartRendererRef = useRef<ChartRendererHandle>(null);

  const collapsed = onToggleCollapse ? isCollapsed : internalCollapsed;
  const toggleCollapse = onToggleCollapse || (() => setInternalCollapsed(!internalCollapsed));

  const displayTableData = tableData;

  return (
    <Collapsible
      open={!collapsed}
      onOpenChange={toggleCollapse}
      style={{ animation: "var(--animate-slideUp)" }}
      className="rounded-lg border bg-card shadow-sm border-l-4 border-l-primary/40"
    >
      {/* Section 1: Query Brief (always visible in header) */}
      <CollapsibleTrigger className="w-full px-6 py-4 flex items-start gap-3 hover:bg-muted/50 transition-all duration-200 ease-in-out">
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="secondary" className="text-xs">
              Data Card
            </Badge>
          </div>
          <div className="font-bold text-sm prose prose-sm dark:prose-invert max-w-none [&>*]:inline [&>*]:m-0">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
              p: ({node, ...props}) => <span {...props} />,
              h1: ({node, ...props}) => <span {...props} />,
              h2: ({node, ...props}) => <span {...props} />,
              h3: ({node, ...props}) => <span {...props} />,
              h4: ({node, ...props}) => <span {...props} />,
              h5: ({node, ...props}) => <span {...props} />,
              h6: ({node, ...props}) => <span {...props} />,
            }}>
              {queryBrief || "Query in progress..."}
            </ReactMarkdown>
          </div>
        </div>
        <ChevronDown
          className={`h-5 w-5 text-muted-foreground shrink-0 transition-transform duration-300 ease-in-out ${
            collapsed ? "-rotate-90" : ""
          }`}
        />
      </CollapsibleTrigger>

      {/* Section 2 & 3: Data Table and AI Explanation */}
      <CollapsibleContent className="px-6 pb-6 space-y-6">
        {/* Code Display (after Brief, before Table) */}
        {generatedCode ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Generated Code</h4>
            <CodeDisplay code={generatedCode} language="python" />
          </div>
        ) : isStreaming ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Generated Code</h4>
            <div className="space-y-2 p-4 border rounded-lg bg-muted/20">
              {/* Skeleton loader for code */}
              <div className="skeleton h-4 w-full rounded" />
              <div className="skeleton h-4 w-5/6 rounded" />
              <div className="skeleton h-4 w-4/5 rounded" />
            </div>
          </div>
        ) : null}

        {/* Section 2: Data Table */}
        {displayTableData ? (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Data Results</h4>
            <div className="max-h-[400px] overflow-y-auto">
              <DataTable columns={displayTableData.columns} data={displayTableData.rows} />
            </div>
            {/* CSV Download below table */}
            {!isStreaming && (
              <div className="flex justify-end">
                <CSVDownloadButton
                  data={displayTableData}
                  filename={queryBrief ? `${queryBrief.toLowerCase().replace(/\s+/g, "-").slice(0, 50)}.csv` : undefined}
                />
              </div>
            )}
          </div>
        ) : isStreaming ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Data Results</h4>
            <div className="space-y-2 p-4 border rounded-lg bg-muted/20">
              {/* Skeleton loader for table */}
              <div className="skeleton h-8 w-full rounded" />
              <div className="skeleton h-6 w-full rounded" />
              <div className="skeleton h-6 w-3/4 rounded" />
            </div>
          </div>
        ) : null}

        {/* Chart Error Alert - subtle dismissible notification */}
        {chartError && !isStreaming && (
          <ChartErrorAlert message={chartError} />
        )}

        {/* Chart Skeleton - shown during chart generation */}
        {visualizationInProgress && !chartSpecs && isStreaming && (
          <ChartSkeleton stage={visualizationStage} />
        )}

        {/* Chart - below table per user decision, fades in smoothly */}
        {chartSpecs && (
          <div
            className="space-y-2"
            style={{ animation: "var(--animate-fadeIn)" }}
          >
            <h4 className="text-sm font-medium text-muted-foreground">
              Visualization
            </h4>
            <ChartRenderer ref={chartRendererRef} data={chartSpecs} />
            {/* Export buttons - only show when not streaming */}
            {!isStreaming && (
              <div className="flex justify-end">
                <ChartExportButtons
                  getChartElement={() => chartRendererRef.current?.getElement() ?? null}
                  filename={queryBrief
                    ? queryBrief.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 30)
                    : undefined
                  }
                />
              </div>
            )}
          </div>
        )}

        {/* Section 3: AI Explanation */}
        {explanation ? (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Analysis</h4>
            <div className="rounded-lg bg-muted/30 p-4">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{explanation}</ReactMarkdown>
              </div>
            </div>
            {/* Markdown Download below explanation */}
            {!isStreaming && (
              <div className="flex justify-end">
                <MarkdownDownloadButton
                  queryBrief={queryBrief || "Analysis"}
                  explanation={explanation}
                  tableData={displayTableData || undefined}
                  filename={queryBrief ? `${queryBrief.toLowerCase().replace(/\s+/g, "-").slice(0, 50)}-analysis.md` : undefined}
                />
              </div>
            )}
          </div>
        ) : isStreaming ? (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Analysis</h4>
            <div className="rounded-lg bg-muted/30 p-4 space-y-2">
              {/* Skeleton loader for explanation */}
              <div className="skeleton h-4 w-full rounded" />
              <div className="skeleton h-4 w-5/6 rounded" />
              <div className="skeleton h-4 w-4/5 rounded" />
            </div>
          </div>
        ) : null}

        {/* Follow-up suggestions */}
        {followUpSuggestions && followUpSuggestions.length > 0 && !isStreaming && (
          <div className="space-y-2 pt-3 border-t border-border/50">
            <h4 className="text-xs font-medium text-muted-foreground">Continue exploring</h4>
            <div className="flex flex-wrap gap-2">
              {followUpSuggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => onFollowUpClick?.(suggestion)}
                  className="px-3 py-1.5 rounded-full border text-xs hover:bg-accent hover:border-primary/30 transition-all duration-200 bg-background cursor-pointer"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Sources section */}
        {searchSources && searchSources.length > 0 && !isStreaming && (
          <div className="space-y-2 pt-3 border-t border-border/50">
            <h4 className="text-xs font-medium text-muted-foreground">Sources</h4>
            <div className="space-y-1">
              {searchSources.map((source, idx) => (
                <a
                  key={idx}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-primary hover:underline truncate group"
                  title={source.url}
                >
                  <ExternalLink className="h-3 w-3 shrink-0 opacity-50 group-hover:opacity-100" />
                  {source.title || source.url}
                </a>
              ))}
            </div>
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}

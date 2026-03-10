"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { SignalChartRenderer } from "@/components/workspace/signal-chart-renderer";
import { Microscope, Wand2, MessageSquare, Loader2, ArrowLeft } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";
import { useCreateSession, useLinkFile } from "@/hooks/useSessionMutations";
import type { SignalDetail, CollectionFile } from "@/types/workspace";

const severityConfig = {
  critical: {
    label: "Critical",
    className:
      "bg-severity-critical/15 text-severity-critical border-severity-critical/30",
  },
  warning: {
    label: "Warning",
    className:
      "bg-severity-warning/15 text-severity-warning border-severity-warning/30",
  },
  info: {
    label: "Informational",
    className:
      "bg-severity-info/15 text-severity-info border-severity-info/30",
  },
} as const;

interface SignalDetailPanelProps {
  signal: SignalDetail | null;
  onBack?: () => void;
  collectionFiles?: CollectionFile[];
  collectionId?: string;
}

export function SignalDetailPanel({ signal, onBack, collectionFiles = [], collectionId }: SignalDetailPanelProps) {
  if (!signal) {
    return (
      <div className="flex-1 flex items-center justify-center h-full">
        <p className="text-sm text-muted-foreground">
          Select a signal to view details
        </p>
      </div>
    );
  }

  const severity = severityConfig[signal.severity];

  const router = useRouter();
  const createSession = useCreateSession();
  const { mutateAsync: linkFileAsync } = useLinkFile();
  const [isBridging, setIsBridging] = useState(false);

  const handleChatBridge = async () => {
    setIsBridging(true);
    try {
      const session = await createSession.mutateAsync("New Chat");
      await Promise.all(
        collectionFiles.map((f) =>
          linkFileAsync({ sessionId: session.id, fileId: f.file_id })
        )
      );
      router.push(`/sessions/${session.id}`);
    } catch {
      toast.error("Failed to open Chat. Please try again.");
    } finally {
      setIsBridging(false);
    }
  };

  return (
    <ScrollArea className="h-full flex-1">
      <div className="p-6 space-y-6 max-w-4xl">
        {/* Mobile back button — only visible below sm breakpoint */}
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors sm:hidden"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Signals
          </button>
        )}

        {/* Header */}
        <div>
          <div className="flex items-start justify-between gap-4 mb-3">
            <h2 className="text-xl font-semibold leading-tight">
              {signal.title}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn("text-xs font-semibold", severity.className)}
            >
              {severity.label}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {signal.category}
            </Badge>
          </div>
        </div>

        {/* Chart */}
        <Card className="py-0 gap-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Visualization
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <SignalChartRenderer key={signal.id} signal={signal} />
          </CardContent>
        </Card>

        {/* Analysis */}
        {signal.analysis && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Analysis
            </h3>
            <div className="prose prose-sm dark:prose-invert max-w-none text-foreground/90">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {signal.analysis}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* Chat bridge */}
        <div>
          <Button
            size="sm"
            variant="outline"
            className="gap-2 w-full"
            onClick={handleChatBridge}
            disabled={isBridging || collectionFiles.length === 0}
          >
            {isBridging ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <MessageSquare className="h-4 w-4" />
            )}
            Chat with Spectra
          </Button>
        </div>

        {/* Evidence Grid */}
        {signal.evidence && (
          <Card className="py-0 gap-0">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Statistical Evidence
              </CardTitle>
            </CardHeader>
            <CardContent className="pb-4">
              <div className="grid grid-cols-2 gap-3">
                {(
                  [
                    { label: "Metric", value: signal.evidence.metric },
                    { label: "Context", value: signal.evidence.context },
                    { label: "Benchmark", value: signal.evidence.benchmark },
                    { label: "Impact", value: signal.evidence.impact },
                  ] as const
                ).map((item) => (
                  <div
                    key={item.label}
                    className="rounded-lg bg-muted/50 px-3 py-2.5"
                  >
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">
                      {item.label}
                    </p>
                    <p className="text-sm font-semibold">{item.value}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="pt-2">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Actions
          </h3>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <Button
                      size="sm"
                      className="gap-2 opacity-50 cursor-not-allowed"
                      disabled
                    >
                      <Microscope className="h-4 w-4" />
                      Investigate
                    </Button>
                  </span>
                </TooltipTrigger>
                <TooltipContent>Coming in a future update</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-2 opacity-50 cursor-not-allowed"
                      disabled
                    >
                      <Wand2 className="h-4 w-4" />
                      What-If Analysis
                    </Button>
                  </span>
                </TooltipTrigger>
                <TooltipContent>Coming in a future update</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}

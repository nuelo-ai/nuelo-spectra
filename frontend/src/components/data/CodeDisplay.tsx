"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Code, Copy, Check, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface CodeDisplayProps {
  code: string;
  language?: string;
}

/**
 * Code Display Component
 * Shows Python code with copy-to-clipboard and collapsible toggle.
 * Starts collapsed - user clicks "View code" to expand.
 */
export function CodeDisplay({ code, language = "python" }: CodeDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy code:", err);
    }
  };

  const lines = code.split("\n");
  const showLineNumbers = lines.length > 3;

  return (
    <div className="space-y-2">
      {/* Toggle button */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <Code className="h-4 w-4" />
          {isExpanded ? "Hide code" : "View code"}
          <ChevronDown
            className={`h-4 w-4 transition-transform ${
              isExpanded ? "rotate-180" : ""
            }`}
          />
        </Button>
      </div>

      {/* Code block (collapsible) */}
      {isExpanded && (
        <div className="relative rounded-lg border bg-slate-900 overflow-hidden">
          {/* Header with language badge and copy button */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700 bg-slate-800">
            <Badge
              variant="outline"
              className="text-xs border-slate-600 text-slate-300"
            >
              {language.toUpperCase()}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-7 gap-2 text-slate-300 hover:text-white hover:bg-slate-700"
            >
              {isCopied ? (
                <>
                  <Check className="h-4 w-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy
                </>
              )}
            </Button>
          </div>

          {/* Code content */}
          <div className="overflow-x-auto">
            <pre className="p-4 text-sm">
              <code className="font-mono text-slate-100">
                {showLineNumbers ? (
                  <div className="flex">
                    {/* Line numbers */}
                    <div className="select-none pr-4 text-slate-500 border-r border-slate-700">
                      {lines.map((_, i) => (
                        <div key={i} className="text-right">
                          {i + 1}
                        </div>
                      ))}
                    </div>
                    {/* Code lines */}
                    <div className="pl-4 flex-1">
                      {lines.map((line, i) => (
                        <div key={i}>{line || " "}</div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="whitespace-pre">{code}</div>
                )}
              </code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

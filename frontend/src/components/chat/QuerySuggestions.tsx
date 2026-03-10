"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  TrendingUp,
  BarChart2,
  Layers,
  Sparkles,
  MessageSquare,
  type LucideIcon,
} from "lucide-react";

interface QuerySuggestionsProps {
  categories: Array<{
    name: string;
    queries: string[];
  }>;
  onSelect: (suggestion: string) => void;
  autoSend?: boolean;
}

function getCategoryIcon(categoryName: string): LucideIcon {
  const lower = categoryName.toLowerCase();
  if (["trend", "growth", "change"].some((kw) => lower.includes(kw))) {
    return TrendingUp;
  }
  if (["compare", "segment", "break"].some((kw) => lower.includes(kw))) {
    return BarChart2;
  }
  if (["summary", "overview", "general"].some((kw) => lower.includes(kw))) {
    return Layers;
  }
  if (["forecast", "predict", "future"].some((kw) => lower.includes(kw))) {
    return Sparkles;
  }
  return MessageSquare;
}

/**
 * Displays grouped query suggestion cards for empty chat state.
 * Suggestions are organized into a responsive multi-column grid — one column per category.
 * Each category column has an icon + uppercase label header.
 * Each suggestion is a Signal-card-style bordered card.
 * Clicking a card fires onSelect and fades out remaining cards.
 */
export function QuerySuggestions({
  categories,
  onSelect,
  autoSend = true,
}: QuerySuggestionsProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [visible, setVisible] = useState(true);
  const [expanded, setExpanded] = useState(false);

  if (!visible) return null;

  const handleClick = (suggestion: string) => {
    setSelected(suggestion);
    onSelect(suggestion);
    // Fade out remaining cards, then hide entirely
    setTimeout(() => {
      setVisible(false);
    }, 300);
  };

  const VISIBLE_COLS = 3;
  const hasMore = categories.length > VISIBLE_COLS;
  const visibleCategories = expanded ? categories : categories.slice(0, VISIBLE_COLS);

  return (
    <div style={{ animation: "var(--animate-fadeIn)" }}>
      <div
        className="grid gap-4 w-full"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}
      >
        {visibleCategories.map((category) => {
          const Icon = getCategoryIcon(category.name);

          return (
            <div key={category.name} className="flex flex-col">
              {/* Column header — fixed min-height keeps all columns aligned */}
              <div className="flex flex-col items-center gap-2 mb-4 pb-3 border-b border-border min-h-[4.5rem]">
                <Icon className="h-5 w-5 text-foreground" />
                <span className="text-xs font-bold uppercase tracking-widest text-foreground text-center">
                  {category.name}
                </span>
              </div>

              {/* Suggestion cards */}
              <div className="flex flex-col gap-2">
                {category.queries.map((suggestion) => {
                  const isSelected = selected === suggestion;
                  const isFadingOut = selected !== null && !isSelected;

                  return (
                    <button
                      key={suggestion}
                      onClick={() => handleClick(suggestion)}
                      disabled={selected !== null}
                      className={[
                        "rounded-lg border p-3 w-full text-left transition-all duration-150",
                        isSelected
                          ? "border-primary bg-primary/5 shadow-sm"
                          : "border-border bg-transparent hover:bg-accent/50 hover:border-primary/30",
                        isFadingOut ? "opacity-0 transition-opacity duration-300" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                    >
                      <span className="text-sm text-foreground leading-snug line-clamp-3 inline [&>strong]:font-semibold">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <>{children}</>,
                          }}
                        >
                          {suggestion}
                        </ReactMarkdown>
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {hasMore && !expanded && (
        <div className="flex justify-center mt-3">
          <button
            onClick={() => setExpanded(true)}
            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1.5 transition-colors"
          >
            <span>View more</span>
            <span className="text-muted-foreground/60">({categories.length - VISIBLE_COLS} more)</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
          </button>
        </div>
      )}
    </div>
  );
}

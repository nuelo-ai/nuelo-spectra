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

  if (!visible) return null;

  const handleClick = (suggestion: string) => {
    setSelected(suggestion);
    onSelect(suggestion);
    // Fade out remaining cards, then hide entirely
    setTimeout(() => {
      setVisible(false);
    }, 300);
  };

  return (
    <div style={{ animation: "var(--animate-fadeIn)" }}>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 w-full max-w-4xl mx-auto">
        {categories.map((category) => {
          const Icon = getCategoryIcon(category.name);

          return (
            <div key={category.name} className="flex flex-col">
              {/* Column header */}
              <div className="flex items-center gap-1.5 mb-3 pb-2 border-b border-border">
                <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
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
    </div>
  );
}

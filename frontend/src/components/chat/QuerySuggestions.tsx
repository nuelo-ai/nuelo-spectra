"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";

interface QuerySuggestionsProps {
  categories: Array<{
    name: string;
    suggestions: string[];
  }>;
  onSelect: (suggestion: string) => void;
  autoSend?: boolean;
}

/**
 * Displays grouped query suggestion chips for empty chat state.
 * Chips are organized by LLM-generated categories.
 * Clicking a chip auto-sends the query (default) or populates the input.
 * After selection, remaining chips fade out over 300ms.
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
    // Fade out remaining chips, then hide entirely
    setTimeout(() => {
      setVisible(false);
    }, 300);
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh] p-8">
      <div
        className="flex flex-col items-center gap-6 max-w-2xl mx-auto"
        style={{ animation: "var(--animate-fadeIn)" }}
      >
        {/* Greeting */}
        <p className="text-muted-foreground text-lg font-medium text-center">
          What would you like to know about your data?
        </p>

        {/* Category groups */}
        {categories.map((category) => (
          <div key={category.name} className="w-full space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground text-center uppercase tracking-wide">
              {category.name}
            </h3>
            <div className="flex flex-wrap justify-center gap-2">
              {category.suggestions.map((suggestion) => {
                const isSelected = selected === suggestion;
                const isFadingOut = selected !== null && !isSelected;

                return (
                  <button
                    key={suggestion}
                    onClick={() => handleClick(suggestion)}
                    disabled={selected !== null}
                    className={`px-4 py-2 rounded-full border text-sm cursor-pointer transition-all duration-300 ${
                      isSelected
                        ? "bg-primary text-primary-foreground border-primary"
                        : isFadingOut
                        ? "opacity-0"
                        : "bg-background hover:bg-accent hover:border-primary/30"
                    }`}
                  >
                    <span className="inline [&>strong]:font-semibold">
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
        ))}
      </div>
    </div>
  );
}

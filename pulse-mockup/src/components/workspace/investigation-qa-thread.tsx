"use client";

import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { QAExchange } from "@/lib/mock-data";

interface InvestigationQAThreadProps {
  exchanges: QAExchange[];
  onSelectChoice: (exchangeId: string, choice: string) => void;
  onFreeText: (exchangeId: string, text: string) => void;
}

export function InvestigationQAThread({
  exchanges,
  onSelectChoice,
  onFreeText,
}: InvestigationQAThreadProps) {
  const [freeTextValues, setFreeTextValues] = useState<Record<string, string>>(
    {}
  );

  // Split exchanges into completed and active
  const completedExchanges = exchanges.filter(
    (ex) => ex.selectedChoice !== null || ex.freeTextAnswer !== null
  );
  const activeExchange =
    exchanges.find(
      (ex) => ex.selectedChoice === null && ex.freeTextAnswer === null
    ) ?? null;

  // If all exchanges are complete and there is no active exchange, render nothing
  if (!activeExchange && completedExchanges.length === exchanges.length && exchanges.length > 0) {
    return null;
  }

  const handleFreeTextChange = (exchangeId: string, text: string) => {
    setFreeTextValues((prev) => ({ ...prev, [exchangeId]: text }));
  };

  const handleFreeTextSubmit = (exchangeId: string) => {
    const text = freeTextValues[exchangeId] ?? "";
    if (text.trim()) {
      onFreeText(exchangeId, text.trim());
      setFreeTextValues((prev) => ({ ...prev, [exchangeId]: "" }));
    }
  };

  return (
    <ScrollArea className="h-full">
      <div className="space-y-4">
        {/* Completed exchanges */}
        {completedExchanges.map((exchange, index) => (
          <div key={exchange.id}>
            <div className="space-y-2">
              {/* AI question */}
              <div>
                <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                  Spectra
                </span>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {exchange.question}
                </p>
              </div>
              {/* User answer */}
              <div>
                <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                  You
                </span>
                <p className="text-sm text-foreground mt-0.5">
                  {exchange.selectedChoice ?? exchange.freeTextAnswer}
                </p>
              </div>
            </div>
            {/* Separator between pairs */}
            {index < completedExchanges.length - 1 && (
              <hr className="border-border/40 mt-4" />
            )}
          </div>
        ))}

        {/* Separator before active exchange */}
        {completedExchanges.length > 0 && activeExchange && (
          <hr className="border-border/40" />
        )}

        {/* Active exchange */}
        {activeExchange && (
          <div className="space-y-4">
            {/* AI question with left accent border */}
            <p className="text-sm font-medium text-foreground leading-relaxed pl-3 border-l-2 border-primary/40">
              {activeExchange.question}
            </p>

            {/* Radio-style choice buttons */}
            <div className="space-y-2">
              {activeExchange.choices.map((choice) => (
                <button
                  key={choice}
                  onClick={() => onSelectChoice(activeExchange.id, choice)}
                  className="border border-border rounded-lg px-4 py-2.5 text-sm text-left w-full hover:border-primary/50 hover:bg-primary/5 transition-colors duration-100"
                >
                  {choice}
                </button>
              ))}
            </div>

            {/* Free-text area */}
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                Or describe in your own words
              </p>
              <div className="flex gap-2 items-end">
                <Textarea
                  placeholder="Add your own answer..."
                  value={freeTextValues[activeExchange.id] ?? ""}
                  onChange={(e) =>
                    handleFreeTextChange(activeExchange.id, e.target.value)
                  }
                  className="flex-1 resize-none"
                  rows={2}
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleFreeTextSubmit(activeExchange.id)}
                  disabled={!(freeTextValues[activeExchange.id] ?? "").trim()}
                >
                  Submit
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}

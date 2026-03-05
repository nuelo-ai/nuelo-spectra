"use client";

// Note: This component relies on React's key prop for scenario switching.
// The parent passes key={selectedScenarioId}, so when the user selects a different
// scenario React unmounts/remounts this component, reinitializing messages from
// the new initialMessages prop automatically — no useEffect reset needed.

import { useEffect, useRef, useState } from "react";
import { SendHorizonal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { WhatIfScenario, WhatIfChatMessage } from "@/lib/mock-data";

interface WhatIfRefinementChatProps {
  scenario: WhatIfScenario;
  initialMessages: WhatIfChatMessage[];
}

export function WhatIfRefinementChat({
  scenario,
  initialMessages,
}: WhatIfRefinementChatProps) {
  const [messages, setMessages] =
    useState<WhatIfChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function handleSend() {
    if (!input.trim()) return;
    const userMsg: WhatIfChatMessage = {
      id: `chat-new-${Date.now()}`,
      role: "user",
      content: input.trim(),
    };
    const aiMsg: WhatIfChatMessage = {
      id: `chat-ai-${Date.now()}`,
      role: "assistant",
      content: `I've updated the scenario based on your input. The core assumptions and confidence level remain the same, but the detail you requested has been incorporated into the narrative and data backing sections.`,
    };
    setMessages((prev) => [...prev, userMsg, aiMsg]);
    setInput("");
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
      {/* Message Thread — fills available space, pins input to bottom */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-3 min-h-0"
      >
        {messages.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">
            Ask Spectra to refine this scenario. E.g., &ldquo;Change the
            timeline to 3 months&rdquo; or &ldquo;Remove the third
            assumption.&rdquo;
          </p>
        ) : (
          messages.map((message) =>
            message.role === "user" ? (
              <div key={message.id} className="flex justify-end">
                <div className="max-w-[85%] rounded-lg bg-primary text-primary-foreground px-3 py-2 text-sm">
                  {message.content}
                </div>
              </div>
            ) : (
              <div key={message.id} className="flex justify-start">
                <div className="max-w-[85%] rounded-lg bg-muted px-3 py-2 text-sm leading-relaxed">
                  {message.content}
                </div>
              </div>
            )
          )
        )}
      </div>

      {/* Chat Input Footer */}
      <div className="px-3 py-3 border-t border-border shrink-0">
        <div className="flex items-end gap-2">
          <Textarea
            placeholder="Refine this scenario..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={2}
            className="flex-1 resize-none text-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <Button
            size="icon"
            variant="default"
            className="shrink-0 h-8 w-8"
            disabled={!input.trim()}
            onClick={handleSend}
          >
            <SendHorizonal className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

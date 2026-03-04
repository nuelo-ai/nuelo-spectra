"use client";

import { useState } from "react";
import { Activity, PlusCircle, Send, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AddToCollectionModal } from "@/components/workspace/add-to-collection-modal";
import { MOCK_CHAT_MESSAGES, ChatResultCard } from "@/lib/mock-data";

// --- Simple markdown renderer for bold text ---
function renderSimpleMarkdown(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

// --- Result card sub-renderers ---
function TableResult({
  data,
}: {
  data: { headers: string[]; rows: string[][] };
}) {
  return (
    <div className="overflow-x-auto p-4">
      <table className="w-full text-sm">
        <thead>
          <tr>
            {data.headers.map((h) => (
              <th
                key={h}
                className="text-left px-3 py-2 font-medium text-muted-foreground border-b border-border"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row, i) => (
            <tr key={i} className="border-b border-border/50 last:border-0">
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-sm">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartPlaceholder({ description }: { description?: string }) {
  return (
    <div className="p-4">
      <div className="h-32 rounded-md bg-[#0a0e1a] border border-border/50 flex items-center justify-center">
        <div className="text-center px-4">
          <BarChart3 className="h-8 w-8 text-primary/30 mx-auto mb-2" />
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
    </div>
  );
}

function TextResult({ content }: { content: string }) {
  return (
    <div className="p-4 text-sm text-foreground leading-relaxed">
      {renderSimpleMarkdown(content)}
    </div>
  );
}

// --- Result card wrapper ---
function ResultCard({
  card,
  onAddToCollection,
}: {
  card: ChatResultCard;
  onAddToCollection: (title: string) => void;
}) {
  return (
    <div className="ml-10 rounded-lg border border-border bg-card overflow-hidden">
      {/* Card header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-[#111827]">
        <span className="text-sm font-medium">{card.title}</span>
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5 h-7 text-xs"
          onClick={() => onAddToCollection(card.title)}
        >
          <PlusCircle className="h-3 w-3" /> Add to Collection
        </Button>
      </div>

      {/* Card content by type */}
      {card.type === "table" && card.tableData && (
        <TableResult data={card.tableData} />
      )}
      {card.type === "chart" && (
        <ChartPlaceholder description={card.chartDescription} />
      )}
      {card.type === "text" && <TextResult content={card.content} />}
    </div>
  );
}

// --- Main Chat page ---
export default function ChatPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalCardTitle, setModalCardTitle] = useState("");

  const handleAddToCollection = (cardTitle: string) => {
    setModalCardTitle(cardTitle);
    setModalOpen(true);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Chat</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Ask questions about your data
        </p>
      </div>

      {/* Messages area */}
      <div className="flex flex-col gap-6 pb-24">
        {MOCK_CHAT_MESSAGES.map((message) => {
          if (message.role === "user") {
            return (
              <div key={message.id} className="flex justify-end">
                <div className="max-w-lg rounded-2xl bg-primary px-4 py-3 text-sm text-primary-foreground">
                  {message.content}
                </div>
              </div>
            );
          }

          // Assistant message
          return (
            <div key={message.id} className="flex flex-col gap-3">
              {/* Assistant prose */}
              <div className="flex items-start gap-3">
                <div className="h-7 w-7 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                  <Activity className="h-3.5 w-3.5 text-primary" />
                </div>
                <p className="text-sm text-foreground pt-0.5">
                  {message.content}
                </p>
              </div>

              {/* Result cards */}
              {message.resultCards?.map((card) => (
                <ResultCard
                  key={card.id}
                  card={card}
                  onAddToCollection={handleAddToCollection}
                />
              ))}
            </div>
          );
        })}
      </div>

      {/* Disabled input bar at bottom */}
      <div className="fixed bottom-0 left-60 right-0 p-4 bg-[#0a0e1a] border-t border-border">
        <div className="max-w-3xl mx-auto flex gap-2">
          <Input
            disabled
            placeholder="Ask a question about your data..."
            className="flex-1"
          />
          <Button disabled size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Add to Collection modal */}
      <AddToCollectionModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        cardTitle={modalCardTitle}
      />
    </div>
  );
}

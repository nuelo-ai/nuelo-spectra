"use client";

import { useAuth } from "@/hooks/useAuth";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { useCreateSession } from "@/hooks/useSessionMutations";
import { useSSEStream } from "@/hooks/useSSEStream";
import { useSearchToggle } from "@/hooks/useSearchToggle";
import { ChatInput } from "@/components/chat/ChatInput";
import { QuerySuggestions } from "@/components/chat/QuerySuggestions";
import { FileLinkingDropdown } from "@/components/file/FileLinkingDropdown";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";

interface WelcomeScreenProps {
  /** If provided, the session already exists (user navigated to /sessions/[id] with no messages yet) */
  sessionId?: string;
}

/**
 * Welcome screen shown when a user starts a new session or has no messages yet.
 * Displays a warm, personalized greeting with the user's first name,
 * an always-active chat input, and query suggestions when files are linked.
 */
export function WelcomeScreen({ sessionId }: WelcomeScreenProps) {
  const { user } = useAuth();
  const router = useRouter();
  const { data: sessionDetail } = useSessionDetail(sessionId ?? null);
  const createSession = useCreateSession();
  const { startStream } = useSSEStream();
  const searchToggle = useSearchToggle();

  const firstName = user?.first_name || "there";
  const linkedFiles = sessionDetail?.files ?? [];
  const hasLinkedFiles = linkedFiles.length > 0;

  const handleSend = async (message: string) => {
    // Case 1: No session yet — create one, then prompt to add file
    if (!sessionId) {
      try {
        const newSession = await createSession.mutateAsync("New Chat");
        router.replace(`/sessions/${newSession.id}`);
        toast.info("Please add a file first to start analyzing your data", {
          duration: 4000,
        });
      } catch {
        toast.error("Failed to create session. Please try again.");
      }
      return;
    }

    // Case 2: Session exists but no linked files
    if (!hasLinkedFiles) {
      toast.info("Please add a file first to start analyzing your data", {
        duration: 4000,
      });
      return;
    }

    // Case 3: Session exists and has linked files — start streaming
    await startStream(sessionId, message, searchToggle.enabled);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Sidebar toggle */}
      <div className="px-4 py-3">
        <SidebarTrigger className="-ml-1" />
      </div>

      {/* Main content area — centered greeting */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-2xl w-full space-y-8 text-center">
          {/* Subtle decorative element */}
          <div className="flex justify-center">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-blue-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-indigo-500/70" />
            </div>
          </div>

          {/* Greeting */}
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">
              Hi {firstName}! What would you like to analyze today?
            </h1>
            {!hasLinkedFiles && (
              <p className="text-muted-foreground text-base">
                Add a file to start exploring your data
              </p>
            )}
          </div>

          {/* Query suggestions when files are linked */}
          {hasLinkedFiles && sessionDetail && (
            <QuerySuggestions
              categories={[]}
              onSelect={(suggestion) => handleSend(suggestion)}
              autoSend={true}
            />
          )}
        </div>
      </div>

      {/* Chat input — fixed at bottom */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <ChatInput
            onSend={handleSend}
            disabled={false}
            searchEnabled={searchToggle.enabled}
            onSearchToggle={searchToggle.toggle}
            searchConfigured={searchToggle.isConfigured}
            searchQuotaExceeded={searchToggle.isQuotaExceeded}
            leftSlot={
              sessionId ? (
                <FileLinkingDropdown
                  sessionId={sessionId}
                  linkedFileIds={linkedFiles.map((f) => f.id)}
                />
              ) : undefined
            }
          />
        </div>
      </div>
    </div>
  );
}

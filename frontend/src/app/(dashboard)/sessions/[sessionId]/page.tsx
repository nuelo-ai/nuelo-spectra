"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { useChatMessages } from "@/hooks/useChatMessages";
import { useGenerateTitle } from "@/hooks/useSessionMutations";
import { useSessionStore } from "@/stores/sessionStore";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { WelcomeScreen } from "@/components/session/WelcomeScreen";

/**
 * Session chat page - renders either WelcomeScreen (no messages yet)
 * or ChatInterface (has messages) for a specific session.
 * Fetches session detail and messages to determine which view to show.
 */
export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const { data: session, isLoading, isError } = useSessionDetail(sessionId);
  const { data: chatData, isLoading: messagesLoading } = useChatMessages(sessionId);
  const { mutate: generateTitle } = useGenerateTitle();
  const setCurrentSession = useSessionStore((s) => s.setCurrentSession);
  const titleGenerated = useRef(false);

  // Update sessionStore.currentSessionId when this page mounts
  useEffect(() => {
    setCurrentSession(sessionId);
    titleGenerated.current = false; // Reset for new session
    return () => {
      setCurrentSession(null);
    };
  }, [sessionId, setCurrentSession]);

  // Generate title after first user message + AI response
  useEffect(() => {
    const messages = chatData?.messages ?? [];
    const shouldGenerate =
      messages.length >= 2 &&
      session?.title === "New Chat" &&
      !session?.user_modified &&
      !titleGenerated.current;

    if (shouldGenerate) {
      titleGenerated.current = true;
      // No message content sent -- backend reads from DB (security)
      generateTitle({ sessionId });
    }
  }, [chatData?.messages, session?.title, session?.user_modified, sessionId, generateTitle]);

  // Loading state
  if (isLoading || messagesLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Error or not found — show error with navigation option (no auto-redirect to avoid loops)
  if (isError || !session) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="text-muted-foreground">Session not found</p>
        <button
          onClick={() => router.push("/sessions/new")}
          className="text-sm text-primary underline hover:no-underline"
        >
          Start a new chat
        </button>
      </div>
    );
  }

  // Show WelcomeScreen when session has no messages yet
  const hasMessages = (chatData?.messages?.length ?? 0) > 0;

  if (!hasMessages) {
    return <WelcomeScreen sessionId={session.id} />;
  }

  return (
    <ChatInterface
      sessionId={session.id}
      sessionTitle={session.title}
    />
  );
}

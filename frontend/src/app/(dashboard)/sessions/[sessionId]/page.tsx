"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { useChatMessages } from "@/hooks/useChatMessages";
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
  const setCurrentSession = useSessionStore((s) => s.setCurrentSession);

  // Update sessionStore.currentSessionId when this page mounts
  useEffect(() => {
    setCurrentSession(sessionId);
    return () => {
      setCurrentSession(null);
    };
  }, [sessionId, setCurrentSession]);

  // Loading state
  if (isLoading || messagesLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Error or not found - redirect to new session
  if (isError || !session) {
    router.push("/sessions/new");
    return null;
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

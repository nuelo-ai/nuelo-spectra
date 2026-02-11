'use client'

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { useSessionStore } from "@/stores/sessionStore";
import { ChatInterface } from "@/components/chat/ChatInterface";

/**
 * Session chat page - renders ChatInterface for a specific session.
 * Fetches session detail and passes sessionId/sessionTitle to ChatInterface.
 */
export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const { data: session, isLoading, isError } = useSessionDetail(sessionId);
  const setCurrentSession = useSessionStore((s) => s.setCurrentSession);

  // Update sessionStore.currentSessionId when this page mounts
  useEffect(() => {
    setCurrentSession(sessionId);
    return () => {
      setCurrentSession(null);
    };
  }, [sessionId, setCurrentSession]);

  // Loading state
  if (isLoading) {
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

  return (
    <ChatInterface
      sessionId={session.id}
      sessionTitle={session.title}
    />
  );
}

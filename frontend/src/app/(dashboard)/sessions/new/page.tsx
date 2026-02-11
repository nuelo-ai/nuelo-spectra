"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useCreateSession } from "@/hooks/useSessionMutations";
import { WelcomeScreen } from "@/components/session/WelcomeScreen";

/**
 * New session page - auto-creates a session on mount and redirects to /sessions/[id].
 * The WelcomeScreen is rendered at /sessions/[id] via the session page when there are no messages.
 * This approach ensures the session always has an ID for file linking and message sending.
 */
export default function NewSessionPage() {
  const router = useRouter();
  const createSession = useCreateSession();
  const creating = useRef(false);

  useEffect(() => {
    // Prevent double-creation in React strict mode
    if (creating.current) return;
    creating.current = true;

    createSession
      .mutateAsync("New Chat")
      .then((session) => {
        router.replace(`/sessions/${session.id}`);
      })
      .catch(() => {
        // If session creation fails, still show the welcome screen
        creating.current = false;
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Show WelcomeScreen while the session is being created
  return <WelcomeScreen />;
}

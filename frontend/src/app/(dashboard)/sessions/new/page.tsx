"use client";

import { WelcomeScreen } from "@/components/session/WelcomeScreen";

/**
 * New session page - shows the welcome screen without creating a session.
 * Session creation is deferred until user's first meaningful interaction
 * (linking a file or sending a message) to avoid empty session spam.
 */
export default function NewSessionPage() {
  return <WelcomeScreen />;
}

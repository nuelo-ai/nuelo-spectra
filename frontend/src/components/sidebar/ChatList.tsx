"use client";

import { Loader2, MessageSquare } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
} from "@/components/ui/sidebar";
import { ChatListItem } from "@/components/sidebar/ChatListItem";
import { useChatSessions } from "@/hooks/useChatSessions";
import { useSessionStore } from "@/stores/sessionStore";

/**
 * Scrollable list of chat sessions displayed in the sidebar.
 * Flat chronological order, most recent first (backend default).
 */
export function ChatList() {
  const { data, isLoading, isError } = useChatSessions();
  const currentSessionId = useSessionStore((s) => s.currentSessionId);

  if (isLoading) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  if (isError) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="px-2 py-6 text-center">
            <p className="text-sm text-muted-foreground">
              Failed to load chat history
            </p>
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  const sessions = data?.sessions ?? [];

  if (sessions.length === 0) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="flex flex-col items-center gap-2 px-2 py-8 text-center group-data-[collapsible=icon]:hidden">
            <MessageSquare className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              No conversations yet
            </p>
            <p className="text-xs text-muted-foreground/70">
              Start a new chat to begin
            </p>
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  return (
    <SidebarGroup>
      <SidebarGroupContent>
        <SidebarMenu>
          {sessions.map((session) => (
            <ChatListItem
              key={session.id}
              session={session}
              isActive={session.id === currentSessionId}
            />
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}

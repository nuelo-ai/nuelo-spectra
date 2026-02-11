"use client";

import { useRouter } from "next/navigation";
import { MessageSquarePlus, FolderOpen } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar";
import { ChatList } from "@/components/sidebar/ChatList";
import { UserSection } from "@/components/sidebar/UserSection";
import { useCreateSession } from "@/hooks/useSessionMutations";

/**
 * Left sidebar component using shadcn Sidebar with collapsible icon mode.
 * Contains: New Chat button, My Files button, scrollable chat list, and user section.
 */
export function ChatSidebar() {
  const router = useRouter();
  const { state } = useSidebar();
  const createSession = useCreateSession();
  const isExpanded = state === "expanded";

  const handleNewChat = async () => {
    try {
      const session = await createSession.mutateAsync("New Chat");
      router.push(`/sessions/${session.id}`);
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const handleMyFiles = () => {
    router.push("/files");
  };

  return (
    <Sidebar collapsible="icon" className="border-r">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="New Chat"
              onClick={handleNewChat}
              disabled={createSession.isPending}
              className="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground active:bg-primary/90 active:text-primary-foreground"
            >
              <MessageSquarePlus className="shrink-0" />
              {isExpanded && <span>New Chat</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton tooltip="My Files" onClick={handleMyFiles}>
              <FolderOpen className="shrink-0" />
              {isExpanded && <span>My Files</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarSeparator />

      <SidebarContent>
        <ChatList />
      </SidebarContent>

      <SidebarSeparator />

      <SidebarFooter>
        <UserSection />
      </SidebarFooter>
    </Sidebar>
  );
}

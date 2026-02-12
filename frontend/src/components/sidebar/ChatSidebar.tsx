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
  SidebarRail,
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar";
import { ChatList } from "@/components/sidebar/ChatList";
import { UserSection } from "@/components/sidebar/UserSection";
/**
 * Left sidebar component using shadcn Sidebar with collapsible icon mode.
 * Contains: New Chat button, My Files button, scrollable chat list, and user section.
 */
export function ChatSidebar() {
  const router = useRouter();
  const { state } = useSidebar();
  const isExpanded = state === "expanded";

  const handleNewChat = () => {
    router.push("/sessions/new");
  };

  const handleMyFiles = () => {
    router.push("/my-files");
  };

  return (
    <Sidebar collapsible="icon" className="border-r">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-1.5 group-data-[collapsible=icon]:hidden">
          <div className="h-7 w-7 rounded-lg gradient-primary flex items-center justify-center">
            <span className="text-sm font-bold text-white">S</span>
          </div>
          <span className="font-semibold text-sm tracking-tight">Spectra</span>
        </div>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="New Chat"
              onClick={handleNewChat}
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
      <SidebarRail />
    </Sidebar>
  );
}

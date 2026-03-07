"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sparkles,
  MessageSquare,
  FolderOpen,
  Settings,
  Shield,
} from "lucide-react";
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
import { useAuth } from "@/hooks/useAuth";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
  external?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Pulse Analysis", href: "/workspace", icon: Sparkles },
  { label: "Chat", href: "/sessions/new", icon: MessageSquare },
  { label: "Files", href: "/my-files", icon: FolderOpen },
  { label: "Settings", href: "/settings", icon: Settings },
  { label: "Admin Panel", href: "/admin", icon: Shield, adminOnly: true, external: true },
];

/**
 * Unified sidebar component shared across all authenticated pages.
 * Shows navigation items, conditional chat history on chat routes,
 * and user section at the bottom.
 */
export function UnifiedSidebar() {
  const pathname = usePathname();
  const { state } = useSidebar();
  const { user } = useAuth();
  const isExpanded = state === "expanded";

  const isActive = (href: string) => {
    if (href === "/workspace") {
      return pathname === "/workspace" || pathname.startsWith("/workspace/");
    }
    if (href === "/sessions/new") {
      return pathname.startsWith("/sessions") || pathname === "/dashboard";
    }
    return pathname === href || pathname.startsWith(href + "/");
  };

  const showChatHistory =
    pathname.startsWith("/sessions") || pathname === "/dashboard";

  // Build admin panel URL: same origin on port 3001
  const getAdminUrl = () => {
    if (typeof window === "undefined") return "/admin";
    const url = new URL(window.location.origin);
    url.port = "3001";
    return url.toString();
  };

  return (
    <Sidebar collapsible="icon" className="border-r border-[#1e293b] bg-[#070b14]">
      <SidebarHeader>
        <SidebarMenu>
          {NAV_ITEMS.map((item) => {
            if (item.adminOnly && !user?.is_admin) return null;

            const active = isActive(item.href);
            const Icon = item.icon;

            if (item.external) {
              return (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    tooltip={item.label}
                    asChild
                    isActive={active}
                  >
                    <a
                      href={getAdminUrl()}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Icon className="shrink-0" />
                      {isExpanded && <span>{item.label}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            }

            return (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton
                  tooltip={item.label}
                  asChild
                  isActive={active}
                  className={
                    active
                      ? "bg-[#3b82f6]/10 text-[#3b82f6] hover:bg-[#3b82f6]/20 hover:text-[#3b82f6]"
                      : ""
                  }
                >
                  <Link href={item.href}>
                    <Icon className="shrink-0" />
                    {isExpanded && <span>{item.label}</span>}
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarHeader>

      {showChatHistory && (
        <>
          <SidebarSeparator />
          <SidebarContent>
            <ChatList />
          </SidebarContent>
        </>
      )}

      <SidebarSeparator />

      <SidebarFooter>
        <UserSection />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}

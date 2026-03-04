"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Activity,
  FolderOpen,
  Code,
  Settings,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Chat", href: "/chat", icon: MessageSquare },
  { label: "Analysis Workspace", href: "/workspace", icon: Activity },
  { label: "Files", href: "/files", icon: FolderOpen },
  { label: "API", href: "/api-keys", icon: Code },
  { label: "Settings", href: "/settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/workspace") {
      return pathname === "/workspace" || pathname.startsWith("/workspace/");
    }
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-sidebar transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex h-14 items-center border-b border-border px-4",
          collapsed ? "justify-center" : "gap-2"
        )}
      >
        {!collapsed && (
          <Link href="/workspace" className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary">
              <Activity className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-sidebar-foreground">
              Spectra
            </span>
          </Link>
        )}
        {collapsed && (
          <Link href="/workspace">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary">
              <Activity className="h-4 w-4 text-primary-foreground" />
            </div>
          </Link>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-3">
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.href);
          const linkContent = (
            <Link
              key={item.href}
              href={item.href === "/workspace" ? item.href : "#"}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "border-l-2 border-primary bg-sidebar-accent text-sidebar-primary ml-0 pl-[10px]"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                collapsed ? "justify-center px-2" : "gap-3"
              )}
            >
              <item.icon
                className={cn(
                  "h-4 w-4 shrink-0",
                  active
                    ? "text-primary"
                    : "text-sidebar-foreground/50 group-hover:text-sidebar-foreground/70"
                )}
              />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );

          if (collapsed) {
            return (
              <Tooltip key={item.href} delayDuration={0}>
                <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                <TooltipContent side="right" sideOffset={8}>
                  {item.label}
                </TooltipContent>
              </Tooltip>
            );
          }

          return linkContent;
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border px-2 py-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className={cn(
            "w-full text-sidebar-foreground/50 hover:text-sidebar-foreground",
            collapsed ? "justify-center px-2" : "justify-start gap-3 px-3"
          )}
        >
          {collapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <>
              <PanelLeftClose className="h-4 w-4" />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </Button>
      </div>

      {/* User section */}
      <div
        className={cn(
          "border-t border-border p-3",
          collapsed ? "flex justify-center" : "flex items-center gap-3"
        )}
      >
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-primary/20 text-xs text-primary">
            DU
          </AvatarFallback>
        </Avatar>
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-sidebar-foreground">
              Demo User
            </p>
            <p className="truncate text-xs text-sidebar-foreground/50">
              demo@spectra.ai
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}

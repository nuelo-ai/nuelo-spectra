"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Moon, Sun, LogOut } from "lucide-react";
import { useTheme } from "next-themes";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const routeTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/users": "Users",
  "/invitations": "Invitations",
  "/credits": "Credits",
  "/settings": "Settings",
  "/audit-log": "Audit Log",
};

function getPageTitle(pathname: string): string {
  // Check exact match first
  if (routeTitles[pathname]) return routeTitles[pathname];

  // Check prefix matches (e.g., /users/123 -> Users)
  for (const [route, title] of Object.entries(routeTitles)) {
    if (pathname.startsWith(route + "/")) return title;
  }

  return "Admin";
}

export function AdminHeader() {
  const pathname = usePathname();
  const { user, logout } = useAdminAuth();
  const { theme, setTheme } = useTheme();

  const pageTitle = getPageTitle(pathname);
  const initials = user
    ? `${(user.first_name || "A")[0]}${(user.last_name || "")[0]}`.toUpperCase()
    : "A";
  const fullName = user
    ? `${user.first_name || ""} ${user.last_name || ""}`.trim() || "Admin"
    : "Admin";

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      <h1 className="text-lg font-semibold text-foreground">{pageTitle}</h1>

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="h-8 w-8"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="relative flex items-center gap-2 px-2"
            >
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium hidden sm:inline-block">
                {fullName}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <div className="px-2 py-1.5">
              <p className="text-sm font-medium">{fullName}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

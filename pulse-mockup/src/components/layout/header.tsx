"use client";

import { useTheme } from "next-themes";
import { Sun, Moon, Bell, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { CREDIT_BALANCE } from "@/lib/mock-data";

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { theme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-sm">
      {/* Left: Page title / breadcrumb */}
      <div className="min-w-0 flex-1">
        {title && (
          <div className="flex items-center gap-2">
            <h1 className="truncate text-sm font-semibold text-foreground">
              {title}
            </h1>
            {subtitle && (
              <>
                <span className="text-muted-foreground">/</span>
                <span className="truncate text-sm text-muted-foreground">
                  {subtitle}
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Right: Credit balance + Theme toggle + Notifications */}
      <div className="flex items-center gap-1">
        {/* Credit balance indicator */}
        <div className="mr-2 flex items-center gap-1.5 rounded-md bg-primary/10 px-3 py-1.5">
          <Zap className="h-3.5 w-3.5 text-primary" />
          <span className="text-sm font-medium text-primary">
            {CREDIT_BALANCE} credits
          </span>
        </div>

        {/* Theme toggle */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
              <span className="sr-only">Toggle theme</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          </TooltipContent>
        </Tooltip>

        {/* Notification bell (decorative) */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <Bell className="h-4 w-4" />
              <span className="sr-only">Notifications</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>Notifications</TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}

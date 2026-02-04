"use client";

import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";

/**
 * Dashboard page - placeholder for now.
 * Will be replaced with file management and chat interface in later plans.
 */
export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold mb-4">Welcome to Spectra</h1>
      <p className="text-muted-foreground mb-8">
        Logged in as: {user?.email}
      </p>
      <Button onClick={logout} variant="outline">
        Log out
      </Button>
    </div>
  );
}

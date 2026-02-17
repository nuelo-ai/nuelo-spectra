"use client";

import { SettingsForm } from "@/components/settings/SettingsForm";
import { usePlatformSettings } from "@/hooks/useSettings";

export default function SettingsPage() {
  const { data, isLoading, error } = usePlatformSettings();

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-destructive">
          Failed to load settings: {error.message}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure platform-wide settings and policies
        </p>
      </div>
      <SettingsForm settings={data} isLoading={isLoading} />
    </div>
  );
}

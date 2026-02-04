"use client";

/**
 * Settings page with profile editing, password change, and account info.
 * Three sections stacked vertically: ProfileForm, PasswordForm, AccountInfo.
 */

import Link from "next/link";
import { ProfileForm } from "@/components/settings/ProfileForm";
import { PasswordForm } from "@/components/settings/PasswordForm";
import { AccountInfo } from "@/components/settings/AccountInfo";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="mx-auto max-w-2xl p-6 space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="mb-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Dashboard
            </Button>
          </Link>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-indigo-600 to-blue-500 bg-clip-text text-transparent">
            Settings
          </h1>
          <p className="text-muted-foreground">
            Manage your account and preferences
          </p>
        </div>

        {/* Settings Sections */}
        <div className="space-y-6">
          <ProfileForm />
          <PasswordForm />
          <AccountInfo />
        </div>
      </div>
    </div>
  );
}

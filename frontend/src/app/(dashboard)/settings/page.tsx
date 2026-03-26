"use client";

import { ProfileForm } from "@/components/settings/ProfileForm";
import { PasswordForm } from "@/components/settings/PasswordForm";
import { AccountInfo } from "@/components/settings/AccountInfo";

export default function SettingsPage() {
  return (
    <div className="max-w-2xl space-y-6">
      <ProfileForm />
      <PasswordForm />
      <AccountInfo />
    </div>
  );
}

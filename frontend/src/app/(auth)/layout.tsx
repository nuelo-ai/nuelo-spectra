"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * Auth layout - centered layout with gradient background for login/register/forgot-password pages.
 * If user is already authenticated, redirects to dashboard.
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  // Show nothing while checking auth state
  if (isLoading || isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 via-slate-50 to-gray-100 dark:from-[#2E3440] dark:via-[#2E3440] dark:to-[#3B4252]">
      <div className="w-full max-w-md px-6">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 dark:from-[#ECEFF4] dark:to-[#D8DEE9] bg-clip-text text-transparent">
            Spectra
          </h1>
          <p className="mt-2 text-muted-foreground">
            AI-powered data analytics
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
